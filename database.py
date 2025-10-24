"""
DATABASE.PY - VERSIÓN SIMPLIFICADA
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Crear conexión a PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def inicializar_bd():
    """Inicializar tabla de subastas (simplificada)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Tabla principal de subastas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subastas (
                id SERIAL PRIMARY KEY,
                id_subasta VARCHAR(100) UNIQUE NOT NULL,
                titulo TEXT,
                descripcion TEXT,
                tipo_bien VARCHAR(100),
                tipo_subasta VARCHAR(100),
                estado VARCHAR(100),
                provincia VARCHAR(100),
                url_detalle TEXT,
                fecha_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para búsquedas rápidas
        cur.execute("CREATE INDEX IF NOT EXISTS idx_provincia ON subastas(provincia)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tipo_bien ON subastas(tipo_bien)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_estado ON subastas(estado)")
        
        conn.commit()
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inicializando BD: {str(e)}")
    finally:
        cur.close()
        conn.close()

def obtener_subastas(filtros=None):
    """Obtener subastas con filtros opcionales"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM subastas WHERE 1=1"
    params = []
    
    if filtros:
        if filtros.get('provincia'):
            query += " AND provincia = %s"
            params.append(filtros['provincia'])
        
        if filtros.get('tipo'):
            query += " AND tipo_bien = %s"
            params.append(filtros['tipo'])
        
        if filtros.get('search'):
            query += " AND (titulo ILIKE %s OR descripcion ILIKE %s)"
            search_term = f"%{filtros['search']}%"
            params.extend([search_term, search_term])
    
    query += " ORDER BY fecha_scraping DESC LIMIT 100"
    
    cur.execute(query, params)
    resultados = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return resultados

def contar_subastas():
    """Contar total de subastas en la BD"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM subastas")
    total = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return total

if __name__ == '__main__':
    inicializar_bd()
