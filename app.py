from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SUBASTAS = [
    {
        "id": 1,
        "id_subasta": "SUB-2025-001234",
        "titulo": "Vivienda en Madrid Centro",
        "descripcion": "Piso 95m², 3 habitaciones, 2 baños, reformado",
        "tipo": "Inmueble",
        "valor": 250000,
        "pujaMinima": 187500,
        "estado": "Abierta",
        "fechaInicio": "2025-09-15",
        "fechaFin": "2025-10-15",
        "provincia": "Madrid",
        "localidad": "Madrid",
        "direccion": "Calle Gran Vía 45, 28013 Madrid",
        "coordenadas": {"lat": 40.4200, "lng": -3.7025},
        "autoridad": "Juzgado Primera Instancia nº 5",
        "lote": "Lote único",
        "imagenes": [
            {"nombre": "fachada.jpg", "url": "https://placehold.co/800x600/3b82f6/white?text=Madrid+Centro"},
            {"nombre": "interior.jpg", "url": "https://placehold.co/800x600/10b981/white?text=Interior"}
        ],
        "documentos": [
            {"nombre": "nota_simple.pdf", "size": "245 KB"},
            {"nombre": "tasacion.pdf", "size": "1.2 MB"}
        ]
    },
    {
        "id": 2,
        "id_subasta": "SUB-2025-001235",
        "titulo": "Mercedes Clase C 220d",
        "descripcion": "Año 2020, 45.000 km, perfecto estado",
        "tipo": "Vehículo",
        "valor": 35000,
        "pujaMinima": 26250,
        "estado": "Abierta",
        "fechaInicio": "2025-09-20",
        "fechaFin": "2025-10-20",
        "provincia": "Barcelona",
        "localidad": "Barcelona",
        "direccion": "Depósito Municipal, Barcelona",
        "coordenadas": {"lat": 41.3543, "lng": 2.1202},
        "autoridad": "Agencia Tributaria Barcelona",
        "lote": "Lote 1 de 3",
        "imagenes": [
            {"nombre": "frontal.jpg", "url": "https://placehold.co/800x600/1e40af/white?text=Mercedes"},
            {"nombre": "lateral.jpg", "url": "https://placehold.co/800x600/1e3a8a/white?text=Vista+Lateral"}
        ],
        "documentos": [
            {"nombre": "ficha_tecnica.pdf", "size": "156 KB"}
        ]
    },
    {
        "id": 3,
        "id_subasta": "SUB-2025-001236",
        "titulo": "Apartamento playa Marbella",
        "descripcion": "65m², 2 habitaciones, vistas al mar",
        "tipo": "Inmueble",
        "valor": 320000,
        "pujaMinima": 240000,
        "estado": "Abierta",
        "fechaInicio": "2025-09-10",
        "fechaFin": "2025-10-10",
        "provincia": "Málaga",
        "localidad": "Marbella",
        "direccion": "Paseo Marítimo 12, Marbella",
        "coordenadas": {"lat": 36.5105, "lng": -4.8854},
        "autoridad": "Juzgado Primera Instancia nº 7",
        "lote": "Lote único",
        "imagenes": [
            {"nombre": "vistas.jpg", "url": "https://placehold.co/800x600/06b6d4/white?text=Vistas+Mar"},
            {"nombre": "salon.jpg", "url": "https://placehold.co/800x600/0891b2/white?text=Salon"}
        ],
        "documentos": [
            {"nombre": "cert_energetico.pdf", "size": "210 KB"}
        ]
    }
]

@app.route('/')
def home():
    return jsonify({
        "message": "Auction Brokers API",
        "status": "running",
        "endpoints": ["/api/health", "/api/subastas"]
    })

@app.route('/api/health')
def health():
    return jsonify({"success": True, "status": "running"})

@app.route('/api/subastas')
def get_subastas():
    provincia = request.args.get('provincia', '')
    tipo = request.args.get('tipo', '')
    search = request.args.get('search', '')
    
    resultados = SUBASTAS
    
    if provincia:
        resultados = [s for s in resultados if s.get('provincia') == provincia]
    if tipo:
        resultados = [s for s in resultados if s.get('tipo') == tipo]
    if search:
        resultados = [s for s in resultados if search.lower() in s.get('titulo', '').lower()]
    
    return jsonify({"success": True, "data": resultados, "total": len(resultados)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
