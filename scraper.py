"""
SCRAPER BOE - VERSIÓN FINAL CORREGIDA
Basado en el HTML real del portal de subastas del BOE
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import re
from datetime import datetime
from database import get_db_connection
import boto3

# =====================================================
# CONFIGURACIÓN
# =====================================================

# AWS S3
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_BUCKET = os.getenv('AWS_BUCKET', 'auctionbrokers-files')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-3')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# URLs del BOE
BASE_URL = 'https://subastas.boe.es'
SEARCH_URL = f'{BASE_URL}/subastas_ava.php'

# Provincias españolas (códigos del 01 al 52)
PROVINCIAS = {
    '28': 'Madrid',
    '08': 'Barcelona',
    '41': 'Sevilla',
    '46': 'Valencia',
    '29': 'Málaga',
    '48': 'Vizcaya',
    '35': 'Las Palmas',
    '07': 'Baleares',
    '03': 'Alicante',
    '30': 'Murcia'
    # Agregar más según necesites
}

# Valores exactos según el HTML del BOE
TIPOS_SUBASTA = {
    'J': 'Judicial',
    'N': 'Notarial',
    'A': 'AEAT',
}

ESTADOS = {
    'EJ': 'Celebrándose',
    'PU': 'Próxima apertura',
}

TIPOS_BIEN = {
    'I': 'Inmuebles',
    'V': 'Vehículos',
    'M': 'Otros bienes'
}

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def buscar_subastas(provincia_cod, tipo_subasta, estado, tipo_bien):
    """
    Busca subastas usando POST tal como lo hace el formulario del BOE
    """
    print(f"🔍 Buscando: {PROVINCIAS.get(provincia_cod, provincia_cod)} | {TIPOS_SUBASTA.get(tipo_subasta, 'Todos')} | {ESTADOS.get(estado, 'Todos')} | {TIPOS_BIEN.get(tipo_bien, 'Todos')}")
    
    # Datos del formulario (según el HTML real que me pasaste)
    payload = {
        'campo[0]': 'ORIGEN',
        'dato[0]': tipo_subasta,
        'campo[2]': 'ESTADO_SUB',
        'dato[2]': estado,
        'campo[3]': 'TIPO_BIEN',
        'dato[3]': tipo_bien,
        'campo[8]': 'BIEN.COD_PROVINCIA',
        'dato[8]': provincia_cod,
        'page_hits': '500',  # Máximo permitido
        'accion': 'Buscar'
    }
    
    try:
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
        
        response = requests.post(SEARCH_URL, data=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"  ❌ Error HTTP {response.status_code}")
            return []
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Verificar si hay error
        error = soup.find('div', class_='error')
        if error:
            print(f"  ⚠️ Error del BOE: {error.get_text(strip=True)}")
            return []
        
        # Buscar resultados (según estructura HTML real)
        resultados = soup.select('li.resultado-busqueda')
        
        if not resultados:
            print(f"  📭 Sin resultados")
            return []
        
        print(f"  ✅ Encontrados: {len(resultados)} resultados")
        
        subastas = []
        for resultado in resultados:
            try:
                # Extraer título (contiene el ID)
                h3 = resultado.find('h3')
                if not h3:
                    continue
                
                titulo_completo = h3.get_text(strip=True)
                
                # Extraer ID de subasta (formato: "SUBASTA SUB-XX-YYYY-NNNNNN")
                match = re.search(r'SUB-[A-Z]{2}-\d{4}-\d+', titulo_completo)
                if not match:
                    continue
                
                id_subasta = match.group(0)
                
                # Extraer URL de detalle
                link = resultado.select_one('a.resultado-busqueda-link-defecto')
                if not link or not link.get('href'):
                    continue
                
                href = link['href']
                if href.startswith('./'):
                    href = href[2:]
                url_detalle = f"{BASE_URL}/{href}"
                
                # Extraer información básica
                h4 = resultado.find('h4')
                autoridad = h4.get_text(strip=True) if h4 else ''
                
                parrafos = resultado.find_all('p')
                estado_texto = ''
                descripcion = ''
                
                for p in parrafos:
                    texto = p.get_text(strip=True)
                    if texto.startswith('Estado:'):
                        estado_texto = texto.replace('Estado:', '').strip()
                    elif texto.startswith('Descripción'):
                        descripcion = texto.replace('Descripción', '').strip()
                
                subastas.append({
                    'id_subasta': id_subasta,
                    'titulo': titulo_completo,
                    'autoridad': autoridad,
                    'estado': estado_texto,
                    'descripcion': descripcion,
                    'url_detalle': url_detalle,
                    'provincia': PROVINCIAS.get(provincia_cod, provincia_cod),
                    'tipo_bien': TIPOS_BIEN.get(tipo_bien, 'Otros'),
                    'tipo_subasta': TIPOS_SUBASTA.get(tipo_subasta, 'Otros')
                })
                
            except Exception as e:
                print(f"  ⚠️ Error parseando resultado: {str(e)}")
                continue
        
        time.sleep(2)  # Pausa entre requests
        return subastas
        
    except requests.exceptions.Timeout:
        print(f"  ⏱️ Timeout en búsqueda")
        return []
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return []

def guardar_subasta_db(subasta_data):
    """
    Guarda una subasta en PostgreSQL
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verificar si ya existe
        cur.execute(
            "SELECT id FROM subastas WHERE id_subasta = %s",
            (subasta_data['id_subasta'],)
        )
        
        if cur.fetchone():
            print(f"    ⏭️ Ya existe: {subasta_data['id_subasta']}")
            return False
        
        # Insertar nueva subasta
        cur.execute("""
            INSERT INTO subastas (
                id_subasta, titulo, descripcion, tipo_bien, tipo_subasta,
                estado, provincia, url_detalle, fecha_scraping
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            subasta_data['id_subasta'],
            subasta_data['titulo'],
            subasta_data['descripcion'],
            subasta_data['tipo_bien'],
            subasta_data['tipo_subasta'],
            subasta_data['estado'],
            subasta_data['provincia'],
            subasta_data['url_detalle'],
            datetime.now()
        ))
        
        conn.commit()
        print(f"    ✅ Guardada: {subasta_data['id_subasta']}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"    ❌ Error BD: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================

def scraping_completo():
    """
    Realiza scraping completo pero inteligente del BOE
    """
    print("=" * 60)
    print("🚀 INICIANDO SCRAPING DEL BOE")
    print("=" * 60)
    
    total_buscadas = 0
    total_guardadas = 0
    total_duplicadas = 0
    total_errores = 0
    
    inicio = datetime.now()
    
    # Procesar cada provincia
    for provincia_cod, provincia_nombre in PROVINCIAS.items():
        print(f"\n📍 === PROVINCIA: {provincia_nombre} ({provincia_cod}) ===")
        
        # Para cada tipo de subasta
        for tipo_subasta_cod, tipo_subasta_nombre in TIPOS_SUBASTA.items():
            
            # Para cada estado
            for estado_cod, estado_nombre in ESTADOS.items():
                
                # Para cada tipo de bien
                for tipo_bien_cod, tipo_bien_nombre in TIPOS_BIEN.items():
                    
                    total_buscadas += 1
                    
                    # Buscar subastas con esta combinación
                    subastas = buscar_subastas(
                        provincia_cod=provincia_cod,
                        tipo_subasta=tipo_subasta_cod,
                        estado=estado_cod,
                        tipo_bien=tipo_bien_cod
                    )
                    
                    # Guardar cada subasta
                    for subasta in subastas:
                        try:
                            if guardar_subasta_db(subasta):
                                total_guardadas += 1
                            else:
                                total_duplicadas += 1
                        except Exception as e:
                            total_errores += 1
                            print(f"    ❌ Error guardando: {str(e)}")
                    
                    time.sleep(1)  # Pausa entre búsquedas
    
    # Resumen final
    duracion = datetime.now() - inicio
    
    print("\n" + "=" * 60)
    print("✅ SCRAPING COMPLETADO")
    print("=" * 60)
    print(f"⏱️  Duración: {duracion}")
    print(f"🔍 Búsquedas realizadas: {total_buscadas}")
    print(f"✅ Subastas nuevas guardadas: {total_guardadas}")
    print(f"⏭️  Subastas duplicadas: {total_duplicadas}")
    print(f"❌ Errores: {total_errores}")
    print("=" * 60)
    
    return {
        'total_buscadas': total_buscadas,
        'total_guardadas': total_guardadas,
        'total_duplicadas': total_duplicadas,
        'total_errores': total_errores,
        'duracion': str(duracion)
    }

if __name__ == '__main__':
    scraping_completo()
