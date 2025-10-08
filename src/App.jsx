import React, { useState, useEffect } from 'react';
import { Search, Download, Calendar, MapPin, Gavel, FileSpreadsheet, Loader2, ExternalLink, Image, FileText, Map, Database, Settings } from 'lucide-react';

// ⚠️ CAMBIA ESTA URL POR LA DE TU BACKEND DE RENDER
const API_URL = 'https://auctionbrokers-backend.onrender.com';

export default function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ tipo: '', provincia: '', valorMin: '', valorMax: '' });
  const [subastas, setSubastas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSubastas, setSelectedSubastas] = useState(new Set());
  const [downloadingExcel, setDownloadingExcel] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [scrapingStatus, setScrapingStatus] = useState('');

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filters.tipo) params.append('tipo', filters.tipo);
      if (filters.provincia) params.append('provincia', filters.provincia);
      
      const response = await fetch(`${API_URL}/api/subastas?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setSubastas(data.data);
      } else {
        alert('Error al obtener subastas');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error conectando con el servidor');
    } finally {
      setLoading(false);
    }
  };

  const iniciarScraping = async () => {
    if (!confirm('⚠️ ADVERTENCIA:\n\nEl scraping completo puede tardar VARIAS HORAS o incluso DÍAS.\n\nProcesará miles de subastas del BOE y descargará todos los archivos.\n\n¿Estás seguro de que quieres iniciarlo?')) {
      return;
    }

    setScrapingStatus('Iniciando scraping...');
    try {
      const response = await fetch(`${API_URL}/api/scraping/iniciar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      
      if (data.success) {
        setScrapingStatus('✅ ' + data.message);
        alert('✅ Scraping iniciado correctamente!\n\n' + data.message + '\n\nPuedes ver el progreso en los Logs de Render.');
      } else {
        setScrapingStatus('❌ Error: ' + (data.error || 'Error desconocido'));
        alert('Error al iniciar scraping: ' + (data.error || 'Error desconocido'));
      }
    } catch (error) {
      console.error('Error:', error);
      setScrapingStatus('❌ Error de conexión');
      alert('Error conectando con el servidor: ' + error.message);
    }
  };

  const abrirGoogleMaps = (direccion, coords) => {
    const url = coords 
      ? `https://www.google.com/maps/search/?api=1&query=${coords.lat},${coords.lng}`
      : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(direccion)}`;
    window.open(url, '_blank');
  };

  const handleExportExcel = async () => {
    setDownloadingExcel(true);
    try {
      const ids = Array.from(selectedSubastas);
      
      const response = await fetch(`${API_URL}/api/exportar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: ids.length > 0 ? ids : [] })
      });
      
      if (!response.ok) throw new Error('Error al generar Excel');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `subastas_boe_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('✅ Excel descargado con éxito!\n\nIncluye las 25 columnas con fórmulas automáticas y enlaces a Google Maps.');
    } catch (error) {
      console.error('Error:', error);
      alert('Error al generar Excel. Por favor, intenta de nuevo.');
    } finally {
      setDownloadingExcel(false);
    }
  };

  const toggleSeleccion = (id) => {
    const newSelected = new Set(selectedSubastas);
    newSelected.has(id) ? newSelected.delete(id) : newSelected.add(id);
    setSelectedSubastas(newSelected);
  };

  const toggleTodos = () => {
    if (selectedSubastas.size === subastas.length) {
      setSelectedSubastas(new Set());
    } else {
      setSelectedSubastas(new Set(subastas.map(s => s.id)));
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Gavel className="w-10 h-10" />
              <div>
                <h1 className="text-3xl font-bold">Auction Brokers</h1>
                <p className="text-blue-200 text-sm">Portal Profesional de Subastas BOE</p>
              </div>
            </div>
            <button
              onClick={() => setShowAdmin(!showAdmin)}
              className="flex items-center gap-2 bg-blue-800 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
              Admin
            </button>
          </div>
        </div>
      </header>

      {showAdmin && (
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="bg-yellow-400 p-3 rounded-lg">
                <Database className="w-8 h-8 text-yellow-900" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Panel de Administración - Scraping BOE</h3>
                <p className="text-gray-700 mb-4">
                  Inicia el proceso de scraping completo del BOE. Este proceso puede tardar <strong>varias horas o días</strong>.
                </p>
                <div className="bg-white rounded-lg p-4 mb-4">
                  <h4 className="font-semibold text-gray-900 mb-2">⚠️ Información importante:</h4>
                  <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                    <li>Procesará todas las provincias de España (52 en total)</li>
                    <li>Extraerá todos los tipos de bienes y estados de subasta</li>
                    <li>Descargará PDFs e imágenes de cada subasta</li>
                    <li>Almacenará todo en la base de datos PostgreSQL y AWS S3</li>
                    <li>Puede consumir recursos significativos del servidor</li>
                  </ul>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    onClick={iniciarScraping}
                    className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-colors shadow-md"
                  >
                    <Database className="w-5 h-5" />
                    Iniciar Scraping Completo
                  </button>
                  {scrapingStatus && (
                    <p className="text-sm font-medium text-gray-700">{scrapingStatus}</p>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-3">
                  💡 Tip: Puedes ver el progreso en tiempo real en los Logs de Render
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Buscar subastas..."
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 outline-none"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <button
              onClick={handleSearch}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold flex items-center gap-2 transition-colors"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
              Buscar
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t">
            <select
              className="border-2 border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-blue-500"
              value={filters.tipo}
              onChange={(e) => setFilters({...filters, tipo: e.target.value})}
            >
              <option value="">Todos los tipos</option>
              <option value="Inmueble">Inmueble</option>
              <option value="Vehículo">Vehículo</option>
            </select>
            <select
              className="border-2 border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-blue-500"
              value={filters.provincia}
              onChange={(e) => setFilters({...filters, provincia: e.target.value})}
            >
              <option value="">Todas las provincias</option>
              <option value="Madrid">Madrid</option>
              <option value="Barcelona">Barcelona</option>
              <option value="Málaga">Málaga</option>
            </select>
            <input
              type="number"
              placeholder="Valor mín (€)"
              className="border-2 border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-blue-500"
              value={filters.valorMin}
              onChange={(e) => setFilters({...filters, valorMin: e.target.value})}
            />
            <input
              type="number"
              placeholder="Valor máx (€)"
              className="border-2 border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-blue-500"
              value={filters.valorMax}
              onChange={(e) => setFilters({...filters, valorMax: e.target.value})}
            />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-4 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <p className="font-semibold text-gray-700">{subastas.length} subastas encontradas</p>
            {subastas.length > 0 && (
              <button
                onClick={toggleTodos}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                {selectedSubastas.size === subastas.length ? 'Deseleccionar todas' : 'Seleccionar todas'}
              </button>
            )}
          </div>
          <button
            onClick={handleExportExcel}
            disabled={subastas.length === 0 || downloadingExcel}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
              subastas.length === 0 || downloadingExcel
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white hover:shadow-lg'
            }`}
          >
            {downloadingExcel ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generando...
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-5 h-5" />
                Descargar Excel
                {selectedSubastas.size > 0 && ` (${selectedSubastas.size})`}
              </>
            )}
          </button>
        </div>

        {loading ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Buscando subastas...</p>
          </div>
        ) : subastas.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No se encontraron subastas</p>
          </div>
        ) : (
          <div className="space-y-6">
            {subastas.map((s) => (
              <div key={s.id} className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow p-6">
                <div className="flex gap-4">
                  <input
                    type="checkbox"
                    checked={selectedSubastas.has(s.id)}
                    onChange={() => toggleSeleccion(s.id)}
                    className="w-5 h-5 text-blue-600 rounded mt-1"
                  />
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">{s.titulo}</h3>
                        <p className="text-sm text-gray-500">ID: {s.id}</p>
                      </div>
                      <span className="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                        {s.estado}
                      </span>
                    </div>

                    <p className="text-gray-600 mb-4">{s.descripcion}</p>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex-1">
                          <p className="text-xs text-blue-600 font-semibold mb-1 flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            UBICACIÓN
                          </p>
                          <p className="text-sm text-gray-800">{s.direccion}</p>
                        </div>
                        <button
                          onClick={() => abrirGoogleMaps(s.direccion, s.coordenadas)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 whitespace-nowrap"
                        >
                          <Map className="w-4 h-4" />
                          Google Maps
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Tipo</p>
                        <p className="font-semibold text-gray-800">{s.tipo_bien}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Valor Tasación</p>
                        <p className="font-semibold text-gray-800">{s.valor_tasacion?.toLocaleString('es-ES')} €</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Puja Mínima</p>
                        <p className="font-semibold text-green-600">{s.puja_minima?.toLocaleString('es-ES')} €</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Ubicación</p>
                        <p className="font-semibold text-gray-800">{s.localidad}, {s.provincia}</p>
                      </div>
                    </div>

                    {s.imagenes && s.imagenes.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-bold text-gray-700 flex items-center gap-2 mb-3">
                          <Image className="w-4 h-4" />
                          Imágenes ({s.imagenes.length})
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {s.imagenes.map((img, idx) => (
                            <div key={idx}>
                              <img
                                src={img.url}
                                alt={img.nombre}
                                className="w-full h-32 object-cover rounded-lg border-2 border-gray-200 cursor-pointer hover:border-blue-500"
                                onClick={() => window.open(img.url, '_blank')}
                              />
                              <p className="text-xs text-gray-600 mt-1 truncate">{img.nombre}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {s.documentos && s.documentos.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-bold text-gray-700 flex items-center gap-2 mb-3">
                          <FileText className="w-4 h-4" />
                          Documentos ({s.documentos.length})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {s.documentos.map((doc, idx) => (
                            <div key={idx} className="flex items-center gap-3 bg-gray-50 border rounded-lg p-3">
                              <div className="bg-red-100 p-2 rounded">
                                <FileText className="w-5 h-5 text-red-600" />
                              </div>
                              <div>
                                <p className="text-sm font-medium">{doc.nombre}</p>
                                <p className="text-xs text-gray-500">{doc.size}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-6 text-sm text-gray-600 border-t pt-3">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>Inicio: {s.fecha_inicio}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>Fin: {s.fecha_conclusion}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <footer className="bg-gray-800 text-white mt-12 py-6 text-center">
        <p className="text-sm text-gray-400">Auction Brokers - Portal Profesional de Subastas BOE</p>
        <p className="text-xs text-gray-500 mt-2">© {new Date().getFullYear()} - Todos los derechos reservados</p>
      </footer>
    </div>
  );
}
