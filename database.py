import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://auctionbrokers_user:q91mV3yzcNE2j34W8zooZ6prhmkwRn9R@dpg-d3hug6m3jp1c73fs9brg-a.frankfurt-postgres.render.com/auctionbrokers')

def get_db_connection():
    """Crear conexión a PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_database():
    """Inicializar tablas en la base de datos"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabla principal de subastas
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subastas (
            id VARCHAR(50) PRIMARY KEY,
            titulo TEXT,
            descripcion TEXT,
            tipo_bien VARCHAR(100),
            tipo_subasta VARCHAR(100),
            estado VARCHAR(100),
            lotes TEXT,
            provincia VARCHAR(100),
            localidad VARCHAR(200),
            direccion TEXT,
            latitud DECIMAL(10, 8),
            longitud DECIMAL(11, 8),
            referencia_catastral VARCHAR(100),
            marca VARCHAR(100),
            modelo VARCHAR(100),
            matricula VARCHAR(50),
            cantidad_reclamada DECIMAL(15, 2),
            valor_tasacion DECIMAL(15, 2),
            valor_subasta DECIMAL(15, 2),
            tramos_pujas DECIMAL(15, 2),
            puja_minima DECIMAL(15, 2),
            puja_maxima DECIMAL(15, 2),
            importe_deposito DECIMAL(15, 2),
            nombre_acreedor TEXT,
            fecha_inicio DATE,
            fecha_conclusion DATE,
            url_detalle TEXT,
            fecha_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de imágenes
    cur.execute('''
        CREATE TABLE IF NOT EXISTS imagenes (
            id SERIAL PRIMARY KEY,
            subasta_id VARCHAR(50) REFERENCES subastas(id) ON DELETE CASCADE,
            nombre VARCHAR(255),
            url_original TEXT,
            url_s3 TEXT,
            size_bytes INTEGER,
            fecha_descarga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de documentos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id SERIAL PRIMARY KEY,
            subasta_id VARCHAR(50) REFERENCES subastas(id) ON DELETE CASCADE,
            nombre VARCHAR(255),
            tipo VARCHAR(50),
            url_original TEXT,
            url_s3 TEXT,
            size_bytes INTEGER,
            fecha_descarga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Índices para mejorar búsquedas
    cur.execute('CREATE INDEX IF NOT EXISTS idx_provincia ON subastas(provincia)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_tipo_bien ON subastas(tipo_bien)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_estado ON subastas(estado)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_fecha_inicio ON subastas(fecha_inicio)')
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

def insertar_subasta(subasta_data):
    """Insertar o actualizar una subasta"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO subastas (
                id, titulo, descripcion, tipo_bien, tipo_subasta, estado, lotes,
                provincia, localidad, direccion, latitud, longitud, referencia_catastral,
                marca, modelo, matricula, cantidad_reclamada, valor_tasacion, valor_subasta,
                tramos_pujas, puja_minima, puja_maxima, importe_deposito, nombre_acreedor,
                fecha_inicio, fecha_conclusion, url_detalle
            ) VALUES (
                %(id)s, %(titulo)s, %(descripcion)s, %(tipo_bien)s, %(tipo_subasta)s, 
                %(estado)s, %(lotes)s, %(provincia)s, %(localidad)s, %(direccion)s,
                %(latitud)s, %(longitud)s, %(referencia_catastral)s, %(marca)s, %(modelo)s,
                %(matricula)s, %(cantidad_reclamada)s, %(valor_tasacion)s, %(valor_subasta)s,
                %(tramos_pujas)s, %(puja_minima)s, %(puja_maxima)s, %(importe_deposito)s,
                %(nombre_acreedor)s, %(fecha_inicio)s, %(fecha_conclusion)s, %(url_detalle)s
            )
            ON CONFLICT (id) DO UPDATE SET
                titulo = EXCLUDED.titulo,
                descripcion = EXCLUDED.descripcion,
                estado = EXCLUDED.estado,
                actualizado = CURRENT_TIMESTAMP
        ''', subasta_data)
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error insertando subasta {subasta_data.get('id')}: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def insertar_imagen(subasta_id, imagen_data):
    """Insertar imagen en la base de datos"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO imagenes (subasta_id, nombre, url_original, url_s3, size_bytes)
            VALUES (%s, %s, %s, %s, %s)
        ''', (subasta_id, imagen_data['nombre'], imagen_data['url_original'], 
              imagen_data['url_s3'], imagen_data['size_bytes']))
        conn.commit()
    except Exception as e:
        print(f"❌ Error insertando imagen: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def insertar_documento(subasta_id, doc_data):
    """Insertar documento en la base de datos"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO documentos (subasta_id, nombre, tipo, url_original, url_s3, size_bytes)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (subasta_id, doc_data['nombre'], doc_data['tipo'], doc_data['url_original'],
              doc_data['url_s3'], doc_data['size_bytes']))
        conn.commit()
    except Exception as e:
        print(f"❌ Error insertando documento: {e}")
        conn.rollback()
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
    
    query += " ORDER BY fecha_inicio DESC"
    
    cur.execute(query, params)
    resultados = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return resultados

def obtener_imagenes_subasta(subasta_id):
    """Obtener todas las imágenes de una subasta"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM imagenes WHERE subasta_id = %s', (subasta_id,))
    imagenes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return imagenes

def obtener_documentos_subasta(subasta_id):
    """Obtener todos los documentos de una subasta"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM documentos WHERE subasta_id = %s', (subasta_id,))
    documentos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return documentos

if __name__ == '__main__':
    init_database()
