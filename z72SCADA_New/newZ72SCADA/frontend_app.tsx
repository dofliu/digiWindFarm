import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Zap, 
  Wind, 
  Thermometer, 
  AlertTriangle, 
  Activity,
  Eye,
  Download,
  Settings,
  Bell
} from 'lucide-react';

// 模擬風機資料
const mockTurbines = [
  { id: 1, name: 'WT-01', lat: 24.1569, lng: 121.2421, status: 'running', power: 1850, windSpeed: 12.5, rpm: 15.2 },
  { id: 2, name: 'WT-02', lat: 24.1580, lng: 121.2435, status: 'running', power: 1920, windSpeed: 13.2, rpm: 16.1 },
  { id: 3, name: 'WT-03', lat: 24.1590, lng: 121.2450, status: 'maintenance', power: 0, windSpeed: 11.8, rpm: 0 },
  { id: 4, name: 'WT-04', lat: 24.1600, lng: 121.2465, status: 'running', power: 1780, windSpeed: 11.9, rpm: 14.8 },
  { id: 5, name: 'WT-05', lat: 24.1610, lng: 121.2480, status: 'fault', power: 0, windSpeed: 12.1, rpm: 0 },
  { id: 6, name: 'WT-06', lat: 24.1620, lng: 121.2495, status: 'running', power: 1950, windSpeed: 13.8, rpm: 16.5 },
  { id: 7, name: 'WT-07', lat: 24.1630, lng: 121.2510, status: 'running', power: 1680, windSpeed: 10.2, rpm: 13.1 },
  { id: 8, name: 'WT-08', lat: 24.1569, lng: 121.2520, status: 'running', power: 1820, windSpeed: 12.8, rpm: 15.6 },
  { id: 9, name: 'WT-09', lat: 24.1580, lng: 121.2535, status: 'running', power: 1890, windSpeed: 13.1, rpm: 15.9 },
  { id: 10, name: 'WT-10', lat: 24.1590, lng: 121.2550, status: 'running', power: 1750, windSpeed: 11.5, rpm: 14.2 },
  { id: 11, name: 'WT-11', lat: 24.1600, lng: 121.2565, status: 'running', power: 1980, windSpeed: 14.2, rpm: 17.1 },
  { id: 12, name: 'WT-12', lat: 24.1610, lng: 121.2580, status: 'running', power: 1650, windSpeed: 10.8, rpm: 13.8 },
  { id: 13, name: 'WT-13', lat: 24.1620, lng: 121.2595, status: 'running', power: 1870, windSpeed: 12.9, rpm: 15.7 },
  { id: 14, name: 'WT-14', lat: 24.1630, lng: 121.2610, status: 'running', power: 1720, windSpeed: 11.2, rpm: 14.5 }
];

// 風機動畫組件
const WindTurbineIcon = ({ turbine, isSelected, onClick }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return '#10B981'; // 綠色
      case 'maintenance': return '#F59E0B'; // 黃色
      case 'fault': return '#EF4444'; // 紅色
      default: return '#6B7280'; // 灰色
    }
  };

  const isAnimated = turbine.status === 'running' && turbine.rpm > 0;

  return (
    <div 
      className={`relative cursor-pointer transform transition-all duration-300 hover:scale-110 ${
        isSelected ? 'scale-125 z-20' : 'z-10'
      }`}
      onClick={() => onClick(turbine)}
      style={{
        position: 'absolute',
        left: `${(turbine.lng - 121.2400) * 2000}px`,
        top: `${(24.1650 - turbine.lat) * 2000}px`,
        transform: 'translate(-50%, -50%)'
      }}
    >
      {/* 風機塔 */}
      <div 
        className="w-1 bg-gray-600 mx-auto"
        style={{ height: '40px' }}
      />
      
      {/* 風機葉片 */}
      <div className="relative -mt-1">
        <div 
          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center ${
            isAnimated ? 'animate-spin' : ''
          }`}
          style={{ 
            borderColor: getStatusColor(turbine.status),
            backgroundColor: isSelected ? getStatusColor(turbine.status) + '20' : 'transparent',
            animationDuration: isAnimated ? `${3 / (turbine.rpm / 10)}s` : '0s'
          }}
        >
          {/* 三個葉片 */}
          <div className="absolute w-full h-full">
            <div 
              className="absolute w-6 h-0.5 origin-right"
              style={{ 
                backgroundColor: getStatusColor(turbine.status),
                transform: 'rotate(0deg) translateX(-12px)',
                top: '50%'
              }}
            />
            <div 
              className="absolute w-6 h-0.5 origin-right"
              style={{ 
                backgroundColor: getStatusColor(turbine.status),
                transform: 'rotate(120deg) translateX(-12px)',
                top: '50%'
              }}
            />
            <div 
              className="absolute w-6 h-0.5 origin-right"
              style={{ 
                backgroundColor: getStatusColor(turbine.status),
                transform: 'rotate(240deg) translateX(-12px)',
                top: '50%'
              }}
            />
          </div>
        </div>
      </div>

      {/* 風機標籤 */}
      <div className="absolute top-12 left-1/2 transform -translate-x-1/2 bg-white rounded px-2 py-1 shadow-md border text-xs whitespace-nowrap">
        <div className="font-semibold">{turbine.name}</div>
        <div className="text-gray-600">{turbine.power}kW</div>
      </div>

      {/* 選中時的詳細資訊 */}
      {isSelected && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-white rounded-lg p-3 shadow-lg border min-w-48 z-30">
          <div className="font-semibold text-lg mb-2">{turbine.name}</div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>狀態:</span>
              <span style={{ color: getStatusColor(turbine.status) }}>
                {turbine.status === 'running' ? '運行中' : 
                 turbine.status === 'maintenance' ? '維護中' : '故障'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>發電量:</span>
              <span>{turbine.power} kW</span>
            </div>
            <div className="flex justify-between">
              <span>風速:</span>
              <span>{turbine.windSpeed} m/s</span>
            </div>
            <div className="flex justify-between">
              <span>轉速:</span>
              <span>{turbine.rpm} RPM</span>
            </div>
          </div>
          <button className="mt-2 w-full bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
            查看詳細
          </button>
        </div>
      )}
    </div>
  );
};

// 主應用程式
const WindFarmMonitoring = () => {
  const [selectedTurbine, setSelectedTurbine] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [realtimeData, setRealtimeData] = useState(mockTurbines);

  // 模擬即時資料更新
  useEffect(() => {
    const interval = setInterval(() => {
      setRealtimeData(prev => prev.map(turbine => ({
        ...turbine,
        power: turbine.status === 'running' ? 
          Math.max(0, turbine.power + (Math.random() - 0.5) * 100) : 0,
        windSpeed: Math.max(0, turbine.windSpeed + (Math.random() - 0.5) * 2),
        rpm: turbine.status === 'running' ? 
          Math.max(0, turbine.rpm + (Math.random() - 0.5) * 2) : 0
      })));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const totalPower = realtimeData.reduce((sum, turbine) => sum + turbine.power, 0);
  const averageWindSpeed = realtimeData.reduce((sum, turbine) => sum + turbine.windSpeed, 0) / realtimeData.length;
  const runningCount = realtimeData.filter(t => t.status === 'running').length;
  const faultCount = realtimeData.filter(t => t.status === 'fault').length;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 頂部導航 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Wind className="w-8 h-8 text-blue-500" />
              <h1 className="text-xl font-bold text-gray-900">風場監控系統</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Bell className="w-6 h-6 text-gray-600 cursor-pointer hover:text-blue-500" />
              <Settings className="w-6 h-6 text-gray-600 cursor-pointer hover:text-blue-500" />
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* 統計卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Zap className="w-8 h-8 text-yellow-500" />
              <div className="ml-4">
                <p className="text-sm text-gray-600">總發電量</p>
                <p className="text-2xl font-bold">{totalPower.toFixed(0)} kW</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Wind className="w-8 h-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm text-gray-600">平均風速</p>
                <p className="text-2xl font-bold">{averageWindSpeed.toFixed(1)} m/s</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Activity className="w-8 h-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm text-gray-600">運行中</p>
                <p className="text-2xl font-bold">{runningCount} / 14</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <div className="ml-4">
                <p className="text-sm text-gray-600">故障數量</p>
                <p className="text-2xl font-bold">{faultCount}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 標籤導航 */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: '風場總覽', icon: MapPin },
                { id: 'turbines', label: '風機列表', icon: Activity },
                { id: 'alerts', label: '告警管理', icon: AlertTriangle },
                { id: 'reports', label: '報表查詢', icon: Download }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
          
          {/* 標籤內容 */}
          <div className="p-6">
            {activeTab === 'overview' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">風場地圖總覽</h3>
                <div className="relative bg-green-100 rounded-lg overflow-hidden" style={{ height: '600px' }}>
                  {/* 背景地圖 */}
                  <div className="absolute inset-0 bg-gradient-to-br from-green-200 to-blue-200">
                    <div className="absolute inset-0 opacity-20">
                      <svg width="100%" height="100%">
                        <defs>
                          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#ffffff" strokeWidth="1"/>
                          </pattern>
                        </defs>
                        <rect width="100%" height="100%" fill="url(#grid)" />
                      </svg>
                    </div>
                  </div>
                  
                  {/* 風機圖標 */}
                  <div className="relative w-full h-full">
                    {realtimeData.map(turbine => (
                      <WindTurbineIcon
                        key={turbine.id}
                        turbine={turbine}
                        isSelected={selectedTurbine?.id === turbine.id}
                        onClick={setSelectedTurbine}
                      />
                    ))}
                  </div>

                  {/* 圖例 */}
                  <div className="absolute top-4 right-4 bg-white rounded-lg p-4 shadow-lg">
                    <h4 className="font-semibold mb-2">狀態圖例</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span>運行中</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                        <span>維護中</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded-full bg-red-500"></div>
                        <span>故障</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'turbines' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">風機詳細清單</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white border border-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">風機編號</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">狀態</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">發電量 (kW)</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">風速 (m/s)</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">轉速 (RPM)</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {realtimeData.map(turbine => (
                        <tr key={turbine.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {turbine.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              turbine.status === 'running' ? 'bg-green-100 text-green-800' :
                              turbine.status === 'maintenance' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {turbine.status === 'running' ? '運行中' : 
                               turbine.status === 'maintenance' ? '維護中' : '故障'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {turbine.power.toFixed(0)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {turbine.windSpeed.toFixed(1)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {turbine.rpm.toFixed(1)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button className="text-blue-600 hover:text-blue-900 mr-3">
                              <Eye className="w-4 h-4" />
                            </button>
                            <button className="text-gray-600 hover:text-gray-900">
                              <Settings className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'alerts' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">告警管理</h3>
                <div className="space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
                      <span className="font-medium text-red-800">高優先級告警</span>
                    </div>
                    <p className="text-red-700 mt-1">WT-05 設備故障，需要立即檢查</p>
                    <p className="text-red-600 text-sm mt-1">2024-12-19 14:30:25</p>
                  </div>
                  
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
                      <span className="font-medium text-yellow-800">中優先級告警</span>
                    </div>
                    <p className="text-yellow-700 mt-1">WT-03 進入維護模式</p>
                    <p className="text-yellow-600 text-sm mt-1">2024-12-19 12:15:10</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'reports' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">資料查詢與報表</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-3">查詢條件</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">時間範圍</label>
                        <div className="grid grid-cols-2 gap-2">
                          <input type="date" className="border border-gray-300 rounded px-3 py-2 text-sm" />
                          <input type="date" className="border border-gray-300 rounded px-3 py-2 text-sm" />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">風機選擇</label>
                        <select className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                          <option>全部風機</option>
                          {realtimeData.map(turbine => (
                            <option key={turbine.id} value={turbine.id}>{turbine.name}</option>
                          ))}
                        </select>
                      </div>
                      <button className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600">
                        查詢資料
                      </button>
                      <button className="w-full bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600 flex items-center justify-center">
                        <Download className="w-4 h-4 mr-2" />
                        匯出 CSV
                      </button>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-3">快速報表</h4>
                    <div className="space-y-2">
                      <button className="w-full text-left p-3 bg-white rounded border hover:bg-gray-50">
                        日發電量報表
                      </button>
                      <button className="w-full text-left p-3 bg-white rounded border hover:bg-gray-50">
                        週維護記錄
                      </button>
                      <button className="w-full text-left p-3 bg-white rounded border hover:bg-gray-50">
                        月告警統計
                      </button>
                      <button className="w-full text-left p-3 bg-white rounded border hover:bg-gray-50">
                        年度效能分析
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WindFarmMonitoring;