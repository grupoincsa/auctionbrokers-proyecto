from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

SUBASTAS = [
    {
        "id": "SUB-2025-001234",
        "titulo": "Vivienda en Madrid Centro",
        "descripcion": "Piso 95m², 3 habitaciones, 2 baños, reformado, zona centro",
        "tipo_bien": "Inmueble",
        "tipo_subasta": "Judicial",
        "estado": "Abierta",
        "lotes": "Lote único",
        "provincia": "Madrid",
        "localidad": "Madrid",
        "direccion": "Calle Gran Vía 45, 28013 Madrid",
        "coordenadas": {"lat": 40.4200, "lng": -3.7025},
        "referencia_catastral": "1234567VK1234N0001AB",
        "marca": "",
        "modelo": "",
        "matricula": "",
        "cantidad_reclamada": 200000,
        "valor_tasacion": 250000,
        "valor_subasta": 250000,
        "tramos_pujas": 2000,
        "puja_minima": 187500,
        "puja_maxima": 250000,
        "importe_deposito": 25000,
        "nombre": "Juzgado Primera Instancia nº 5 de Madrid",
        "fecha_inicio": "2025-09-15",
        "fecha_conclusion": "2025-10-15",
        "imagenes": [
            {"nombre": "fachada.jpg", "url": "https://placehold.co/800x600/3b82f6/white?text=Madrid"},
            {"nombre": "interior.jpg", "url": "https://placehold.co/800x600/10b981/white?text=Interior"}
        ],
        "documentos": [
            {"nombre": "nota_simple.pdf", "size": "245 KB"},
            {"nombre": "tasacion.pdf", "size": "1.2 MB"}
        ]
    },
    {
        "id": "SUB-2025-001235",
        "titulo": "Mercedes Clase C 220d",
        "descripcion": "Año 2020, 45.000 km, perfecto estado, ITV pasada, único dueño",
        "tipo_bien": "Vehículo",
        "tipo_subasta": "Notarial",
        "estado": "Abierta",
        "lotes": "Lote 1 de 3",
        "provincia": "Barcelona",
        "localidad": "Barcelona",
        "direccion": "Depósito Municipal Zona Franca, Barcelona",
        "coordenadas": {"lat": 41.3543, "lng": 2.1202},
        "referencia_catastral": "",
        "marca": "Mercedes-Benz",
        "modelo": "Clase C 220d",
        "matricula": "1234-ABC",
        "cantidad_reclamada": 30000,
        "valor_tasacion": 35000,
        "valor_subasta": 35000,
        "tramos_pujas": 500,
        "puja_minima": 26250,
        "puja_maxima": 35000,
        "importe_deposito": 3500,
        "nombre": "Agencia Tributaria - Barcelona",
        "fecha_inicio": "2025-09-20",
        "fecha_conclusion": "2025-10-20",
        "imagenes": [
            {"nombre": "frontal.jpg", "url": "https://placehold.co/800x600/1e40af/white?text=Mercedes"},
            {"nombre": "lateral.jpg", "url": "https://placehold.co/800x600/1e3a8a/white?text=Lateral"}
        ],
        "documentos": [
            {"nombre": "ficha_tecnica.pdf", "size": "156 KB"}
        ]
    },
    {
        "id": "SUB-2025-001236",
        "titulo": "Apartamento primera línea playa Marbella",
        "descripcion": "65m², 2 habitaciones, vistas al mar, terraza 20m², piscina comunitaria",
        "tipo_bien": "Inmueble",
        "tipo_subasta": "Judicial",
        "estado": "Abierta",
        "lotes": "Lote único",
        "provincia": "Málaga",
        "localidad": "Marbella",
        "direccion": "Paseo Marítimo Rey de España 12, 29602 Marbella",
        "coordenadas": {"lat": 36.5105, "lng": -4.8854},
        "referencia_catastral": "9876543VK9876N0001CD",
        "marca": "",
        "modelo": "",
        "matricula": "",
        "cantidad_reclamada": 280000,
        "valor_tasacion": 320000,
        "valor_subasta": 320000,
        "tramos_pujas": 3000,
        "puja_minima": 240000,
        "puja_maxima": 320000,
        "importe_deposito": 32000,
        "nombre": "Juzgado Primera Instancia nº 7 de Málaga",
        "fecha_inicio": "2025-09-10",
        "fecha_conclusion": "2025-10-10",
        "imagenes": [
            {"nombre": "vistas.jpg", "url": "https://placehold.co/800x600/06b6d4/white?text=Vistas"},
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
        "version": "2.0",
        "endpoints": ["/api/health", "/api/subastas", "/api/exportar"]
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
        resultados = [s for s in resultados if s.get('tipo_bien') == tipo]
    if search:
        resultados = [s for s in resultados if search.lower() in s.get('titulo', '').lower()]
    
    return jsonify({"success": True, "data": resultados, "total": len(resultados)})

@app.route('/api/exportar', methods=['POST'])
def exportar_excel():
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        
        if not ids:
            subastas_exportar = SUBASTAS
        else:
            subastas_exportar = [s for s in SUBASTAS if s.get('id') in ids]
        
        # Crear Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Subastas BOE"
        
        # Estilos
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Encabezados (25 columnas exactas)
        headers = [
            "RATIO 1 - cantidad reclamada vs valor subasta",
            "RATIO 2 - Puja Máxima vs Valor Subasta",
            "Estado",
            "Tipo De Subasta",
            "Tipo Bien",
            "Id",
            "Lotes",
            "Provincia",
            "Localidad",
            "Dirección",
            "Boton google maps",
            "Descripción",
            "Referencia Catastral",
            "Marca",
            "Modelo",
            "Matricula",
            "Cantidad Reclamada",
            "Valor De Tasacion",
            "Valor Subasta",
            "Tramos Entre Pujas",
            "Puja Mínima",
            "Puja Máxima",
            "Importe Del Deposito",
            "Nombre",
            "Fecha De Inicio",
            "Fecha De Conclusión"
        ]
        
        # Escribir encabezados
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Escribir datos
        for row_num, subasta in enumerate(subastas_exportar, 2):
            coords = subasta.get('coordenadas', {})
            google_maps_url = ""
            if coords and coords.get('lat') and coords.get('lng'):
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={coords['lat']},{coords['lng']}"
            
            # RATIO 1: Fórmula de Excel
            ws.cell(row=row_num, column=1).value = f"=IF(Q{row_num}=0,0,(Q{row_num}/S{row_num})*100)"
            ws.cell(row=row_num, column=1).number_format = '0.00"%"'
            
            # RATIO 2: Fórmula de Excel
            ws.cell(row=row_num, column=2).value = f"=IF(V{row_num}=0,0,(V{row_num}/S{row_num})*100)"
            ws.cell(row=row_num, column=2).number_format = '0.00"%"'
            
            # Resto de columnas
            ws.cell(row=row_num, column=3).value = subasta.get('estado', '')
            ws.cell(row=row_num, column=4).value = subasta.get('tipo_subasta', '')
            ws.cell(row=row_num, column=5).value = subasta.get('tipo_bien', '')
            ws.cell(row=row_num, column=6).value = subasta.get('id', '')
            ws.cell(row=row_num, column=7).value = subasta.get('lotes', '')
            ws.cell(row=row_num, column=8).value = subasta.get('provincia', '')
            ws.cell(row=row_num, column=9).value = subasta.get('localidad', '')
            ws.cell(row=row_num, column=10).value = subasta.get('direccion', '')
            
            # Google Maps como hipervínculo
            if google_maps_url:
                cell = ws.cell(row=row_num, column=11)
                cell.value = "Ver en Google Maps"
                cell.hyperlink = google_maps_url
                cell.font = Font(color="0563C1", underline="single")
            
            ws.cell(row=row_num, column=12).value = subasta.get('descripcion', '')
            ws.cell(row=row_num, column=13).value = subasta.get('referencia_catastral', '')
            ws.cell(row=row_num, column=14).value = subasta.get('marca', '')
            ws.cell(row=row_num, column=15).value = subasta.get('modelo', '')
            ws.cell(row=row_num, column=16).value = subasta.get('matricula', '')
            ws.cell(row=row_num, column=17).value = subasta.get('cantidad_reclamada', 0)
            ws.cell(row=row_num, column=18).value = subasta.get('valor_tasacion', 0)
            ws.cell(row=row_num, column=19).value = subasta.get('valor_subasta', 0)
            ws.cell(row=row_num, column=20).value = subasta.get('tramos_pujas', 0)
            ws.cell(row=row_num, column=21).value = subasta.get('puja_minima', 0)
            ws.cell(row=row_num, column=22).value = subasta.get('puja_maxima', 0)
            ws.cell(row=row_num, column=23).value = subasta.get('importe_deposito', 0)
            ws.cell(row=row_num, column=24).value = subasta.get('nombre', '')
            ws.cell(row=row_num, column=25).value = subasta.get('fecha_inicio', '')
            ws.cell(row=row_num, column=26).value = subasta.get('fecha_conclusion', '')
        
        # Ajustar anchos de columna
        column_widths = [35, 35, 12, 15, 12, 18, 15, 12, 15, 40, 20, 50, 25, 15, 15, 12, 18, 18, 15, 18, 15, 15, 18, 40, 15, 18]
        for col_num, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col_num)].width = width
        
        # Congelar primera fila
        ws.freeze_panes = "A2"
        
        # Añadir filtros
        ws.auto_filter.ref = ws.dimensions
        
        # Guardar archivo temporal
        os.makedirs('temp', exist_ok=True)
        filename = f'temp/subastas_boe_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb.save(filename)
        
        return send_file(
            filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'subastas_boe_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
