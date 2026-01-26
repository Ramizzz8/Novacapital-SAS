import React, { useState } from 'react';
import {
  LayoutDashboard,
  FileText,
  Calculator,
  Users,
  Building2,
  FileSpreadsheet,
  CreditCard,
  UserCog,
  Receipt,
  ChevronDown,
  Bell,
  User,
  TrendingUp,
  TrendingDown,
  MoreVertical,
  Calendar
} from 'lucide-react';

export default function NovacapitalAdmin() {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [expandedMenus, setExpandedMenus] = useState({
    clientes: false,
    plantillas: false,
    pld: false,
    usuarios: false
  });

  const toggleMenu = (menu) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menu]: !prev[menu]
    }));
  };

  // Datos de ejemplo para las gráficas
  const clientesActivosData = [90, 45, 100, 35, 95, 75, 240, 140, 85, 50, 275, 120];
  const mesesLabels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

  const creditosDesembolsadosData = [20, 45, 60, 75, 80, 85, 90];
  const diasLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const maxClientes = Math.max(...clientesActivosData);
  const maxCreditos = Math.max(...creditosDesembolsadosData);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-72 bg-gradient-to-b from-blue-900 to-blue-800 text-white flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-blue-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <span className="text-blue-900 font-bold text-xl">N</span>
            </div>
            <div>
              <h1 className="text-xl font-bold">NOVACAPITAL</h1>
            </div>
          </div>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 overflow-y-auto py-6">
          <div className="space-y-1 px-3">
            {/* Dashboard */}
            <button
              onClick={() => setActiveMenu('dashboard')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                activeMenu === 'dashboard'
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-700/50'
              }`}
            >
              <LayoutDashboard size={20} />
              <span className="font-medium">Dashboard</span>
            </button>

            {/* Reportes */}
            <button
              onClick={() => setActiveMenu('reportes')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                activeMenu === 'reportes'
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-700/50'
              }`}
            >
              <FileText size={20} />
              <span className="font-medium">Reportes</span>
            </button>

            {/* Simulador */}
            <button
              onClick={() => setActiveMenu('simulador')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                activeMenu === 'simulador'
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-700/50'
              }`}
            >
              <Calculator size={20} />
              <span className="font-medium">Simulador</span>
            </button>

            {/* Clientes */}
            <div>
              <button
                onClick={() => toggleMenu('clientes')}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition ${
                  activeMenu === 'clientes'
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-100 hover:bg-blue-700/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Users size={20} />
                  <span className="font-medium">Clientes</span>
                </div>
                <ChevronDown
                  size={16}
                  className={`transition-transform ${expandedMenus.clientes ? 'rotate-180' : ''}`}
                />
              </button>
              {expandedMenus.clientes && (
                <div className="ml-9 mt-1 space-y-1">
                  <button className="w-full text-left px-4 py-2 text-sm text-blue-100 hover:text-white">
                    Lista de Clientes
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-blue-100 hover:text-white">
                    Nuevo Cliente
                  </button>
                </div>
              )}
            </div>

            {/* Campañas */}
            <button
              onClick={() => setActiveMenu('campanas')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                activeMenu === 'campanas'
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-700/50'
              }`}
            >
              <Building2 size={20} />
              <span className="font-medium">Campañas</span>
            </button>

            {/* Plantillas */}
            <div>
              <button
                onClick={() => toggleMenu('plantillas')}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition ${
                  activeMenu === 'plantillas'
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-100 hover:bg-blue-700/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <FileSpreadsheet size={20} />
                  <span className="font-medium">Plantillas</span>
                </div>
                <ChevronDown
                  size={16}
                  className={`transition-transform ${expandedMenus.plantillas ? 'rotate-180' : ''}`}
                />
              </button>
            </div>

            {/* PLD */}
            <div>
              <button
                onClick={() => toggleMenu('pld')}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition ${
                  activeMenu === 'pld'
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-100 hover:bg-blue-700/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <CreditCard size={20} />
                  <span className="font-medium">PLD</span>
                </div>
                <ChevronDown
                  size={16}
                  className={`transition-transform ${expandedMenus.pld ? 'rotate-180' : ''}`}
                />
              </button>
            </div>

            {/* Usuarios y roles */}
            <div>
              <button
                onClick={() => toggleMenu('usuarios')}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition ${
                  activeMenu === 'usuarios'
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-100 hover:bg-blue-700/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <UserCog size={20} />
                  <span className="font-medium">Usuarios y roles</span>
                </div>
                <ChevronDown
                  size={16}
                  className={`transition-transform ${expandedMenus.usuarios ? 'rotate-180' : ''}`}
                />
              </button>
            </div>

            {/* Bitácora */}
            <button
              onClick={() => setActiveMenu('bitacora')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                activeMenu === 'bitacora'
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-700/50'
              }`}
            >
              <Receipt size={20} />
              <span className="font-medium">Bitácora</span>
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Dashboard</p>
              <h1 className="text-2xl font-bold text-blue-900">Vista general de tu empresa</h1>
            </div>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                <Bell size={20} />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <User className="text-white" size={20} />
                </div>
                <span className="font-medium text-gray-700">Leo López</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Cartera Vigente */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-blue-900">Cartera Vigente</h2>
                <button className="text-gray-400 hover:text-gray-600">
                  <MoreVertical size={20} />
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Monto</p>
                  <div className="flex items-center justify-between">
                    <p className="text-3xl font-bold text-gray-900">$124,043.00</p>
                    <div className="flex items-center gap-1 bg-green-100 text-green-700 px-3 py-1 rounded-lg">
                      <TrendingUp size={16} />
                      <span className="text-sm font-semibold">32%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500 mb-1">Monto cobrado</p>
                  <div className="flex items-center justify-between">
                    <p className="text-3xl font-bold text-gray-900">$37,943.00</p>
                    <div className="flex items-center gap-1 bg-green-100 text-green-700 px-3 py-1 rounded-lg">
                      <TrendingUp size={16} />
                      <span className="text-sm font-semibold">24%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Clientes Activos Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-4xl font-bold text-blue-900">724</h2>
                  <p className="text-gray-500">Clientes Activos</p>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Calendar size={16} />
                  <span>Enero 2022 - Diciembre 2022</span>
                  <ChevronDown size={16} />
                </div>
              </div>

              <div className="relative h-64">
                <div className="absolute inset-0 flex items-end justify-between gap-2">
                  {clientesActivosData.map((value, index) => (
                    <div key={index} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-blue-900 rounded-t-md transition-all hover:bg-blue-700"
                        style={{ height: `${(value / maxClientes) * 100}%` }}
                      ></div>
                      <span className="text-xs text-gray-500 mt-2">{mesesLabels[index]}</span>
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-xs text-gray-400 text-right mt-4">Última actualización: 14-noviembre-2022</p>
            </div>

            {/* Cartera en Mora */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-blue-900">Cartera en Mora</h2>
                <button className="text-gray-400 hover:text-gray-600">
                  <MoreVertical size={20} />
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Monto</p>
                  <div className="flex items-center justify-between">
                    <p className="text-3xl font-bold text-gray-900">$24,043.00</p>
                    <div className="flex items-center gap-1 bg-red-100 text-red-700 px-3 py-1 rounded-lg">
                      <TrendingDown size={16} />
                      <span className="text-sm font-semibold">12%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500 mb-1">Monto recuperado</p>
                  <div className="flex items-center justify-between">
                    <p className="text-3xl font-bold text-gray-900">$17,943.00</p>
                    <div className="flex items-center gap-1 bg-green-100 text-green-700 px-3 py-1 rounded-lg">
                      <TrendingUp size={16} />
                      <span className="text-sm font-semibold">32%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Créditos Desembolsados Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-4xl font-bold text-blue-900">598</h2>
                  <p className="text-gray-500">Créditos desembolsados</p>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Calendar size={16} />
                  <span>Enero 2022 - Diciembre 2022</span>
                  <ChevronDown size={16} />
                </div>
              </div>

              <div className="relative h-64">
                <svg className="w-full h-full" viewBox="0 0 700 200" preserveAspectRatio="none">
                  {/* Grid lines */}
                  {[0, 25, 50, 75, 100].map((percent) => (
                    <line
                      key={percent}
                      x1="0"
                      y1={200 - (percent * 2)}
                      x2="700"
                      y2={200 - (percent * 2)}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />
                  ))}

                  {/* Line chart */}
                  <path
                    d={`M 0,${200 - (creditosDesembolsadosData[0] / maxCreditos * 180)} ${creditosDesembolsadosData.map((value, index) =>
                      `L ${(index * 700) / (creditosDesembolsadosData.length - 1)},${200 - (value / maxCreditos * 180)}`
                    ).join(' ')}`}
                    fill="none"
                    stroke="#1e40af"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  {/* Data points */}
                  {creditosDesembolsadosData.map((value, index) => (
                    <circle
                      key={index}
                      cx={(index * 700) / (creditosDesembolsadosData.length - 1)}
                      cy={200 - (value / maxCreditos * 180)}
                      r="4"
                      fill="#1e40af"
                    />
                  ))}

                  {/* Tooltip for last point */}
                  <g transform={`translate(${(6 * 700) / 6}, ${200 - (creditosDesembolsadosData[6] / maxCreditos * 180) - 35})`}>
                    <rect x="-25" y="0" width="50" height="25" rx="4" fill="#1e3a8a" />
                    <text x="0" y="17" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">598</text>
                  </g>
                </svg>

                {/* X-axis labels */}
                <div className="flex justify-between mt-2">
                  {diasLabels.map((label, index) => (
                    <span key={index} className="text-xs text-gray-500">{label}</span>
                  ))}
                </div>
              </div>
              <p className="text-xs text-gray-400 text-right mt-4">Última actualización: 14-noviembre-2022</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
