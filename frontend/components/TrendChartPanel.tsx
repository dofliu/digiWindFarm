import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';

// Colors for up to 8 lines
const LINE_COLORS = ['#22d3ee', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

// Commonly used tag groups
const TAG_PRESETS: Record<string, { label_en: string; label_zh: string; tags: string[] }> = {
  power: {
    label_en: 'Power & Wind',
    label_zh: '功率與風速',
    tags: ['WTUR_TotPwrAt', 'WMET_WSpeedNac'],
  },
  temperature: {
    label_en: 'Temperatures',
    label_zh: '溫度監控',
    tags: ['WGEN_GnStaTmp1', 'WGEN_GnBrgTmp1', 'WGEN_GnAirTmp1', 'WCNV_CnvCabinTmp', 'WGDC_TrfCoreTmp'],
  },
  vibration: {
    label_en: 'Vibration & RPM',
    label_zh: '振動與轉速',
    tags: ['WNAC_VibMsNacXDir', 'WNAC_VibMsNacYDir', 'WROT_RotSpd'],
  },
  pitch: {
    label_en: 'Blade Angles',
    label_zh: '葉片角度',
    tags: ['WROT_PtAngValBl1', 'WROT_PtAngValBl2', 'WROT_PtAngValBl3'],
  },
  converter: {
    label_en: 'Converter',
    label_zh: '變頻器',
    tags: ['WCNV_CnvGnPwr', 'WCNV_CnvGnFrq', 'WCNV_IGCTWtrTmp', 'WCNV_IGCTWtrPres1'],
  },
  yaw: {
    label_en: 'Yaw System',
    label_zh: '轉向系統',
    tags: ['WYAW_YwVn1AlgnAvg5s', 'WYAW_YwBrkHyPrs', 'WYAW_CabWup'],
  },
};

interface TrendChartPanelProps {
  turbineId: string;  // e.g. "WT001"
  lang?: 'en' | 'zh';
}

const TrendChartPanel: React.FC<TrendChartPanelProps> = ({ turbineId, lang = 'zh' }) => {
  const [activePreset, setActivePreset] = useState('power');
  const [customTags, setCustomTags] = useState('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [activeTags, setActiveTags] = useState<string[]>(TAG_PRESETS.power.tags);
  const [tagLabels, setTagLabels] = useState<Record<string, string>>({});

  // Fetch i18n labels
  useEffect(() => {
    fetch(`${API_BASE}/api/i18n/tags?lang=${lang}`)
      .then(r => r.json()).then(setTagLabels).catch(() => {});
  }, [lang]);

  // Fetch trend data
  const fetchTrend = useCallback(() => {
    if (!activeTags.length) return;
    const tagsParam = activeTags.join(',');
    fetch(`${API_BASE}/api/turbines/${turbineId}/trend?tags=${tagsParam}&limit=120`)
      .then(r => r.json())
      .then(res => {
        if (res.data) {
          setChartData(res.data.map((d: any) => ({
            ...d,
            _time: d.timestamp ? new Date(d.timestamp).getTime() : 0,
          })));
        }
      })
      .catch(() => {});
  }, [turbineId, activeTags]);

  useEffect(() => {
    fetchTrend();
    const iv = setInterval(fetchTrend, 2000);
    return () => clearInterval(iv);
  }, [fetchTrend]);

  const handlePreset = (presetId: string) => {
    setActivePreset(presetId);
    setActiveTags(TAG_PRESETS[presetId].tags);
  };

  const handleCustomApply = () => {
    const tags = customTags.split(',').map(t => t.trim()).filter(Boolean);
    if (tags.length) {
      setActivePreset('');
      setActiveTags(tags);
    }
  };

  const getLabel = (tag: string) => tagLabels[tag] || tag;

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
      <h3 className="text-lg font-bold text-white mb-3">
        {lang === 'zh' ? '即時趨勢圖' : 'Real-time Trend'}
      </h3>

      {/* Preset buttons */}
      <div className="flex flex-wrap gap-2 mb-3">
        {Object.entries(TAG_PRESETS).map(([id, preset]) => (
          <button key={id} onClick={() => handlePreset(id)}
            className={`text-xs px-3 py-1 rounded border transition-colors ${
              activePreset === id
                ? 'bg-cyan-600 border-cyan-500 text-white'
                : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-cyan-400'
            }`}>
            {lang === 'zh' ? preset.label_zh : preset.label_en}
          </button>
        ))}
      </div>

      {/* Custom tag input */}
      <div className="flex gap-2 mb-4">
        <input type="text" value={customTags} onChange={e => setCustomTags(e.target.value)}
          placeholder={lang === 'zh' ? '自訂標籤 (逗號分隔)' : 'Custom tags (comma-separated)'}
          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white" />
        <button onClick={handleCustomApply}
          className="bg-gray-600 hover:bg-gray-500 text-white text-xs px-3 py-1 rounded transition-colors">
          {lang === 'zh' ? '套用' : 'Apply'}
        </button>
      </div>

      {/* Chart */}
      <div className="bg-gray-900/50 rounded p-2">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <XAxis
              dataKey="_time"
              tickFormatter={(t) => t ? new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
              stroke="#6b7280"
              fontSize={10}
              axisLine={false}
              tickLine={false}
            />
            <YAxis stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(17,24,39,0.95)', border: '1px solid #374151', borderRadius: '0.5rem', color: '#e5e7eb' }}
              labelFormatter={(t) => t ? new Date(t).toLocaleTimeString() : ''}
              formatter={(value: number, name: string) => [
                value != null ? value.toFixed(2) : '--',
                getLabel(name),
              ]}
            />
            <Legend formatter={(value) => getLabel(value)} wrapperStyle={{ fontSize: '11px' }} />
            {activeTags.map((tag, i) => (
              <Line key={tag} type="monotone" dataKey={tag} stroke={LINE_COLORS[i % LINE_COLORS.length]}
                strokeWidth={1.5} dot={false} isAnimationActive={false} connectNulls />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Active tags reference */}
      <div className="mt-2 text-xs text-gray-500">
        {lang === 'zh' ? '顯示標籤' : 'Tags'}: {activeTags.map(t => getLabel(t)).join(' | ')}
      </div>
    </div>
  );
};

export default TrendChartPanel;
