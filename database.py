"""
DATABASE.PY - VERSIÓN CORREGIDA Y COMPATIBLE
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Crear conexión a PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_database():
    """Inicializar tabla de subastas (nombre compatible con app.py)"""
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
                fecha_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Campos adicionales para compatibilidad con app.py
                fecha_inicio TIMESTAMP,
                fecha_conclusion TIMESTAMP,
                actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lotes TEXT,
                localidad VARCHAR(200),
                direccion TEXT,
                referencia_catastral VARCHAR(100),
                marca VARCHAR(100),
                modelo VARCHAR(100),
                matricula VARCHAR(50),
                cantidad_reclamada DECIMAL(12,2),
                valor_tasacion DECIMAL(12,2),
                valor_subasta DECIMAL(12,2),
                tramos_pujas DECIMAL(12,2),
                puja_minima DECIMAL(12,2),
                puja_maxima DECIMAL(12,2),
                importe_deposito DECIMAL(12,2),
                nombre_acreedor TEXT,
                latitud DECIMAL(10,8),
                longitud DECIMAL(11,8)
            )
        """)
        
        # Tabla de imágenes (para compatibilidad con app.py)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS imagenes (
                id SERIAL PRIMARY KEY,
                subasta_id INTEGER REFERENCES subastas(id) ON DELETE CASCADE,
                nombre VARCHAR(255),
                url_original TEXT,
                url_s3 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de documentos (para compatibilidad con app.py)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id SERIAL PRIMARY KEY,
                subasta_id INTEGER REFERENCES subastas(id) ON DELETE CASCADE,
                nombre VARCHAR(255),
                url_original TEXT,
                url_s3 TEXT,
                size_bytes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para búsquedas rápidas
        cur.execute("CREATE INDEX IF NOT EXISTS idx_provincia ON subastas(provincia)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tipo_bien ON subastas(tipo_bien)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_estado ON subastas(estado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_id_subasta ON subastas(id_subasta)")
        
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
        
        if filtros.get('tipo_bien'):
            query += " AND tipo_bien = %s"
            params.append(filtros['tipo_bien'])
        
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

def obtener_imagenes_subasta(subasta_id):
    """Obtener imágenes de una subasta"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM imagenes 
        WHERE subasta_id = %s 
        ORDER BY created_at ASC
    """, (subasta_id,))
    
    imagenes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return imagenes

def obtener_documentos_subasta(subasta_id):
    """Obtener documentos de una subasta"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM documentos 
        WHERE subasta_id = %s 
        ORDER BY created_at ASC
    """, (subasta_id,))
    
    documentos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return documentos

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
    init_database()
