
import requests
from bs4 import BeautifulSoup
import boto3
from datetime import datetime
import time
import os
import re
from database import insertar_subasta, insertar_imagen, insertar_documento

# Configuración AWS S3
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

# Configuración del scraper
BASE_URL = 'https://subastas.boe.es'
SEARCH_URL = f'{BASE_URL}/subastas_ava.php'

# Provincias españolas
PROVINCIAS = [
    'Álava', 'Albacete', 'Alicante', 'Almería', 'Asturias', 'Ávila', 'Badajoz',
    'Baleares', 'Barcelona', 'Burgos', 'Cáceres', 'Cádiz', 'Cantabria', 'Castellón',
    'Ceuta', 'Ciudad Real', 'Córdoba', 'Cuenca', 'Gerona', 'Granada', 'Guadalajara',
    'Guipúzcoa', 'Huelva', 'Huesca', 'Jaén', 'La Coruña', 'La Rioja', 'Las Palmas',
    'León', 'Lérida', 'Lugo', 'Madrid', 'Málaga', 'Melilla', 'Murcia', 'Navarra',
    'Orense', 'Palencia', 'Pontevedra', 'Salamanca', 'Santa Cruz de Tenerife', 'Segovia',
    'Sevilla', 'Soria', 'Tarragona', 'Teruel', 'Toledo', 'Valencia', 'Valladolid',
    'Vizcaya', 'Zamora', 'Zaragoza'
]

TIPOS_BIEN = [
    'Inmuebles - Vivienda',
    'Inmuebles - Local comercial',
    'Inmuebles - Garaje',
    'Inmuebles - Trastero',
    'Inmuebles - Nave industrial',
    'Inmuebles - Solar',
    'Inmuebles - Finca rústica',
    'Inmuebles - Otros',
    'Vehículos - Turismos',
    'Vehículos - Vehículos industriales',
    'Vehículos - Otros',
    'Otros bienes muebles - Aeronaves',
    'Otros bienes muebles - Buques',
    'Otros bienes muebles - Maquinaria',
    'Otros bienes muebles - Joyas, obras de arte',
    'Otros bienes muebles - Mobiliario',
    'Otros bienes muebles - Otros'
]

TIPOS_SUBASTA = [
    'Judicial',
    'Notarial',
    'AEAT',
    'Otras administraciones tributarias',
    'Subastas administrativas generales'
]

ESTADOS = [
    'Próxima apertura',
    'Celebrándose',
    'Concluida en el portal de subastas',
    'Finalizada por autoridad gestora'
]

def subir_archivo_s3(archivo_bytes, ruta_s3, content_type='application/octet-stream'):
    """Subir archivo a AWS S3"""
    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=ruta_s3,
            Body=archivo_bytes,
            ContentType=content_type,
            ACL='public-read'
        )
        url_s3 = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{ruta_s3}"
        return url_s3
    except Exception as e:
        print(f"❌ Error subiendo a S3: {e}")
        return None

def descargar_archivo(url):
    """Descargar archivo desde URL"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
        return None

def limpiar_texto(texto):
    """Limpiar y normalizar texto"""
    if not texto:
        return ''
    return ' '.join(texto.strip().split())

def extraer_numero(texto):
    """Extraer número de texto"""
    if not texto:
        return 0
    numeros = re.findall(r'[\d,.]+', texto.replace('.', '').replace(',', '.'))
    return float(numeros[0]) if numeros else 0

def parsear_detalle_subasta(url_detalle):
    """Extraer información detallada de una subasta"""
    try:
        response = requests.get(url_detalle, timeout=30)
        soup = BeautifulSoup(response.content, 'lxml')
        
        datos = {
            'id': '',
            'titulo': '',
            'descripcion': '',
            'tipo_bien': '',
            'tipo_subasta': '',
            'estado': '',
            'lotes': '',
            'provincia': '',
            'localidad': '',
            'direccion': '',
            'latitud': None,
            'longitud': None,
            'referencia_catastral': '',
            'marca': '',
            'modelo': '',
            'matricula': '',
            'cantidad_reclamada': 0,
            'valor_tasacion': 0,
            'valor_subasta': 0,
            'tramos_pujas': 0,
            'puja_minima': 0,
            'puja_maxima': 0,
            'importe_deposito': 0,
            'nombre_acreedor': '',
            'fecha_inicio': None,
            'fecha_conclusion': None,
            'url_detalle': url_detalle
        }
        
        # Extraer ID de la URL
        match_id = re.search(r'idSub=([^&]+)', url_detalle)
        if match_id:
            datos['id'] = match_id.group(1)
        
        # Extraer título
        titulo_elem = soup.find('h1')
        if titulo_elem:
            datos['titulo'] = limpiar_texto(titulo_elem.text)
        
        # Extraer campos de la tabla de información
        filas = soup.find_all('tr')
        for fila in filas:
            celdas = fila.find_all(['td', 'th'])
            if len(celdas) >= 2:
                campo = limpiar_texto(celdas[0].text).lower()
                valor = limpiar_texto(celdas[1].text)
                
                if 'descripción' in campo:
                    datos['descripcion'] = valor
                elif 'tipo de bien' in campo:
                    datos['tipo_bien'] = valor
                elif 'tipo de subasta' in campo:
                    datos['tipo_subasta'] = valor
                elif 'estado' in campo:
                    datos['estado'] = valor
                elif 'lote' in campo:
                    datos['lotes'] = valor
                elif 'provincia' in campo:
                    datos['provincia'] = valor
                elif 'localidad' in campo:
                    datos['localidad'] = valor
                elif 'dirección' in campo:
                    datos['direccion'] = valor
                elif 'referencia catastral' in campo:
                    datos['referencia_catastral'] = valor
                elif 'marca' in campo:
                    datos['marca'] = valor
                elif 'modelo' in campo:
                    datos['modelo'] = valor
                elif 'matrícula' in campo:
                    datos['matricula'] = valor
                elif 'cantidad reclamada' in campo:
                    datos['cantidad_reclamada'] = extraer_numero(valor)
                elif 'valor de tasación' in campo or 'valor tasación' in campo:
                    datos['valor_tasacion'] = extraer_numero(valor)
                elif 'valor subasta' in campo or 'valor de subasta' in campo:
                    datos['valor_subasta'] = extraer_numero(valor)
                elif 'tramo' in campo:
                    datos['tramos_pujas'] = extraer_numero(valor)
                elif 'puja mínima' in campo:
                    datos['puja_minima'] = extraer_numero(valor)
                elif 'puja máxima' in campo:
                    datos['puja_maxima'] = extraer_numero(valor)
                elif 'importe del depósito' in campo or 'depósito' in campo:
                    datos['importe_deposito'] = extraer_numero(valor)
                elif 'acreedor' in campo or 'autoridad' in campo:
                    datos['nombre_acreedor'] = valor
                elif 'fecha de inicio' in campo or 'apertura' in campo:
                    try:
                        datos['fecha_inicio'] = datetime.strptime(valor, '%d/%m/%Y').date()
                    except:
                        pass
                elif 'fecha de conclusión' in campo or 'cierre' in campo:
                    try:
                        datos['fecha_conclusion'] = datetime.strptime(valor, '%d/%m/%Y').date()
                    except:
                        pass
        
        # Geocodificar dirección si existe
        if datos['direccion']:
            try:
                direccion_completa = f"{datos['direccion']}, {datos['localidad']}, {datos['provincia']}, España"
                coords = geocodificar_direccion(direccion_completa)
                if coords:
                    datos['latitud'] = coords['lat']
                    datos['longitud'] = coords['lng']
            except:
                pass
        
        return datos
        
    except Exception as e:
        print(f"❌ Error parseando detalle: {e}")
        return None

def geocodificar_direccion(direccion):
    """Obtener coordenadas de Google Maps (Nominatim como alternativa gratuita)"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': direccion,
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'AuctionBrokers/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lng': float(data[0]['lon'])
                }
    except:
        pass
    return None

def descargar_archivos_subasta(subasta_id, soup):
    """Descargar imágenes y documentos de una subasta"""
    imagenes = []
    documentos = []
    
    # Buscar imágenes
    imgs = soup.find_all('img', class_=re.compile('foto|imagen|gallery'))
    for idx, img in enumerate(imgs):
        src = img.get('src')
        if src and not src.startswith('data:'):
            if not src.startswith('http'):
                src = f"{BASE_URL}/{src}"
            
            archivo = descargar_archivo(src)
            if archivo:
                extension = src.split('.')[-1].split('?')[0]
                nombre = f"imagen_{idx + 1}.{extension}"
                ruta_s3 = f"subastas/{subasta_id}/imagenes/{nombre}"
                
                url_s3 = subir_archivo_s3(archivo, ruta_s3, f'image/{extension}')
                if url_s3:
                    imagen_data = {
                        'nombre': nombre,
                        'url_original': src,
                        'url_s3': url_s3,
                        'size_bytes': len(archivo)
                    }
                    imagenes.append(imagen_data)
                    insertar_imagen(subasta_id, imagen_data)
    
    # Buscar documentos PDF
    links = soup.find_all('a', href=re.compile(r'\.pdf|documento', re.I))
    for idx, link in enumerate(links):
        href = link.get('href')
        if href:
            if not href.startswith('http'):
                href = f"{BASE_URL}/{href}"
            
            archivo = descargar_archivo(href)
            if archivo:
                nombre = link.text.strip() or f"documento_{idx + 1}.pdf"
                nombre = re.sub(r'[^\w\s-]', '', nombre)[:100] + '.pdf'
                ruta_s3 = f"subastas/{subasta_id}/documentos/{nombre}"
                
                url_s3 = subir_archivo_s3(archivo, ruta_s3, 'application/pdf')
                if url_s3:
                    doc_data = {
                        'nombre': nombre,
                        'tipo': 'pdf',
                        'url_original': href,
                        'url_s3': url_s3,
                        'size_bytes': len(archivo)
                    }
                    documentos.append(doc_data)
                    insertar_documento(subasta_id, doc_data)
    
    return imagenes, documentos

def buscar_subastas(provincia, tipo_bien, tipo_subasta, estado):
    """Buscar subastas con filtros específicos"""
    try:
        params = {
            'campo[0]': 'PROVINCIA',
            'dato[0]': provincia,
            'campo[1]': 'TIPO_BIEN',
            'dato[1]': tipo_bien,
            'campo[2]': 'TIPO_SUBASTA',
            'dato[2]': tipo_subasta,
            'campo[3]': 'ESTADO',
            'dato[3]': estado
        }
        
        response = requests.get(SEARCH_URL, params=params, timeout=30)
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Buscar enlaces a detalles de subastas
        enlaces = soup.find_all('a', href=re.compile(r'detalleSubasta\.php'))
        urls_detalle = []
        
        for enlace in enlaces:
            href = enlace.get('href')
            if href:
                if not href.startswith('http'):
                    href = f"{BASE_URL}/{href}"
                if href not in urls_detalle:
                    urls_detalle.append(href)
        
        return urls_detalle
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return []

def scraping_completo():
    """Realizar scraping completo del BOE"""
    print("🚀 Iniciando scraping completo del BOE...")
    total_subastas = 0
    
    for provincia in PROVINCIAS:
        print(f"\n📍 Scraping provincia: {provincia}")
        
        for tipo_bien in TIPOS_BIEN:
            for tipo_subasta in TIPOS_SUBASTA:
                for estado in ESTADOS:
                    print(f"  🔍 {tipo_bien} | {tipo_subasta} | {estado}")
                    
                    urls = buscar_subastas(provincia, tipo_bien, tipo_subasta, estado)
                    
                    for url in urls:
                        try:
                            print(f"    ⬇️  Procesando: {url[:80]}...")
                            
                            # Parsear detalle
                            datos = parsear_detalle_subasta(url)
                            if datos and datos['id']:
                                # Guardar en base de datos
                                if insertar_subasta(datos):
                                    total_subastas += 1
                                    
                                    # Descargar archivos
                                    response = requests.get(url, timeout=30)
                                    soup = BeautifulSoup(response.content, 'lxml')
                                    descargar_archivos_subasta(datos['id'], soup)
                                    
                                    print(f"    ✅ Subasta guardada: {datos['id']}")
                            
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"    ❌ Error: {e}")
                    
                    time.sleep(2)
    
    print(f"\n✅ Scraping completo finalizado. Total: {total_subastas} subastas")

if __name__ == '__main__':
    scraping_completo()
