# digiWindFarm — 離岸風力發電場數位孿生模擬系統

整合物理模擬、故障注入、SCADA 監控、Modbus TCP 的風場數位孿生平台。
可作為故障診斷 RAG 系統、資料分析、和運維人員訓練的數據來源。

## 功能特色

- **40 個 SCADA 點位** — 對齊 Bachmann Z72 原廠 OPC 標籤定義
- **真實物理模型** — 模組化子系統：功率曲線(Region 2/3)、校正熱模型、5源振動、偏航死區
- **7 種故障場景** — 漸進式劣化曲線，可供分析師診斷訓練和 RAG 應用
- **9 種風況情境** — 平靜/中等/額定/強風/暴風/陣風/漸增/漸減 + 自訂
- **可設定風機規格** — 切入/額定/切出風速、額定功率、功率曲線、限載
- **操作控制** — 單機停機/啟動/復位/定檢模式/限載（對齊 Modbus Coil）
- **Modbus TCP 模擬器** — 自動啟動 port 5020，外部 SCADA 可直連
- **OPC DA 介接** — 支援 Bachmann Z72、Vestas CK1/CK2 真實風場
- **React 前端** — 3 種儀表板模式、6 個子系統面板、趨勢圖、故障注入、中英文切換
- **CSV 匯出** — 40 個標籤展開成獨立欄位，直接餵 pandas 分析

## 快速開始

```bash
# 後端 (port 8000) + Modbus TCP (port 5020) — 自動啟動
pip install -r requirements.txt
python run.py

# 前端 (port 3000, 另一個終端)
cd frontend
npm install
npm run dev
```

打開 http://localhost:3000 → Settings → 選 "Physics Simulation" → Save

## 系統架構

```
┌─ 物理模型 (simulator/physics/) ────────────────────────┐
│  turbine_physics.py  ← 主模型 (組合 6 個獨立子模型)     │
│  ├─ power_curve.py   ← 功率曲線 + 轉速控制             │
│  ├─ thermal_model.py ← 10 點校正熱模型                 │
│  ├─ vibration_model.py ← 5 源振動模型                  │
│  ├─ yaw_model.py     ← 偏航 (死區+延遲+解纜)           │
│  ├─ wind_field.py    ← 湍流 (AR1/Kaimal) + 尾流        │
│  ├─ fault_engine.py  ← 7 種故障場景                    │
│  └─ scada_registry.py ← 40 標籤 + i18n                │
├─ 風況模型 (wind_model.py) ─────────────────────────── │
│  Auto 日變化 / 9 預設情境 / 自訂覆寫                    │
└──────────────┬─────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │ DataBroker   │  統一介面 (模擬 ↔ OPC DA)
        └──────┬──────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  FastAPI (port 8000)       │  Modbus TCP (port 5020) │
│  REST + WebSocket          │  pymodbus, 14 slaves    │
│  /turbines, /faults,       │  65 registers/slave     │
│  /config, /control, /i18n  │  對齊 Bachmann HldReg   │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  React 19 Frontend (port 3000)                       │
│  卡片/摘要/列表 儀表板 │ 6 子系統面板 │ 趨勢圖        │
│  故障注入 │ 風況設定 │ 風機規格 │ 操作控制 │ 中英文    │
└──────────────────────────────────────────────────────┘
```

## 物理模型子系統

每個子模型是**獨立 class**，可單獨替換升級：

| 子模型 | 檔案 | 說明 |
|--------|------|------|
| **PowerCurveModel** | power_curve.py | 30+ 點查表, Region 2 (V³成長) / Region 3 (恆定功率) |
| **RotorSpeedModel** | power_curve.py | Region 2 最佳 TSR 追蹤, Region 3 恆定 RPM, 慣性 τ=8s |
| **ThermalSystem** | thermal_model.py | 10 個校正熱元件, 穩態: 定子60°C 軸承53°C 變壓器59°C |
| **VibrationModel** | vibration_model.py | 5 源: 1P旋轉 + 3P葉片通過 + 氣動 + 負載 + 寬頻噪聲 |
| **YawModel** | yaw_model.py | 死區±8°, 啟動延遲60s, 保持30s, 解纜±2.5圈 |
| **TurbulenceGenerator** | wind_field.py | AR(1) Kaimal 近似 (τ=L/V, L=340m), 非白噪聲 |
| **PerTurbineWind** | wind_field.py | 空間去相關 + 尾流效應 (2-6% 減損) |

```python
# 替換子模型範例
model = TurbinePhysicsModel()
model.vibration = MyAdvancedVibrationModel()  # 替換振動模型
model.thermal = CFDBasedThermalSystem()       # 替換熱模型
```

### 功率曲線驗證 (5MW Z72, 穩態)
```
風速    功率    轉速   Pitch  發電機溫度  軸承溫度
 3m/s      0kW    0.0    90°    31°C      29°C    ← 切入以下
 7m/s   1068kW    8.0     0°    31°C      32°C    ← Region 2
12m/s   4851kW   13.6     0°    52°C      47°C    ← 額定
18m/s   4900kW   13.6    16°    59°C      53°C    ← Region 3
25m/s   4900kW   13.6    30°    60°C      55°C    ← 切出邊界
26m/s      0kW    0.0    90°     --        --     ← 暴風停機
```

## API 總覽

| 分類 | 端點 | 說明 |
|------|------|------|
| 風機數據 | `GET /api/turbines` | 全部風機即時數據 (51 欄位) |
| | `GET /api/turbines/{id}/trend?tags=TAG1,TAG2` | 多標籤趨勢數據 |
| 風況控制 | `POST /api/config/wind` | 設定風況情境或自訂值 |
| 風機規格 | `GET/POST /api/config/turbine-spec` | 查看/設定風機規格 |
| 操作控制 | `POST /api/control/command` | 停機/啟動/復位/定檢 |
| | `POST /api/control/curtail` | 單機限載 |
| 故障注入 | `POST /api/faults/inject` | 注入故障場景 |
| | `GET /api/faults/active` | 查看活躍故障 |
| i18n | `GET /api/i18n/tags?lang=zh` | SCADA 標籤多語言 |
| Modbus | `GET /api/modbus/registers` | 完整 register map |
| 匯出 | `GET /api/export/history?turbine_id=WT001&format=csv` | CSV 下載 (40 欄) |
| WebSocket | `ws://localhost:8000/ws/realtime` | 即時推送 (2秒) |

完整 API 文件：`http://localhost:8000/docs` (Swagger UI)

## 預設風機規格

| 型號 | 額定功率 | 葉輪直徑 | 切入 | 額定 | 切出 |
|------|---------|---------|------|------|------|
| z72_5mw (預設) | 5 MW | 126 m | 3 m/s | 12 m/s | 25 m/s |
| vestas_v90_3mw | 3 MW | 90 m | 4 m/s | 13 m/s | 25 m/s |
| sg_8mw | 8 MW | 167 m | 3 m/s | 12 m/s | 25 m/s |
| goldwind_2.5mw | 2.5 MW | 121 m | 3 m/s | 10.3 m/s | 22 m/s |

## 故障場景

| 場景 | 影響標籤 | 劣化模式 |
|------|---------|---------|
| 發電機軸承磨損 | 軸承溫度↑ 振動↑ | 指數型 |
| 齒輪箱過熱 | 機艙溫度↑ 振動↑ | 對數型 |
| 葉片變槳馬達劣化 | 葉片角度偏差 功率↓ | 線性 |
| 變頻器冷卻故障 | IGCT水溫↑ 功率↓ | 指數型 |
| 轉向系統偏差 | 偏航誤差↑ 功率↓ | 線性 |
| 發電機超速 | 轉速↑ 振動↑ | 指數型(快) |
| 變壓器過熱 | 變壓器溫度↑ | 對數型 |

## 技術棧

- **後端**: Python 3.10+, FastAPI, uvicorn, numpy, pymodbus, pydantic
- **前端**: React 19, TypeScript, Vite, Tailwind CSS, Recharts
- **資料庫**: SQLite (自動建立)
- **工業協定**: Modbus TCP, OPC DA (OpenOPC2)

## 資料分析用途

模擬器產生的數據可用於：
- **故障診斷訓練** — 注入故障後觀察漸進劣化趨勢
- **RAG 知識庫** — SCADA 標籤定義 + 告警碼 + 故障 SOP
- **功率曲線分析** — wind speed vs power scatter plot
- **健康評估** — 溫度/振動長期趨勢分析
- **ML 模型訓練** — CSV 匯出直接餵 pandas/scikit-learn

```bash
# 匯出 CSV 供分析
curl "http://localhost:8000/api/export/history?turbine_id=WT001&format=csv&limit=50000" -o WT001.csv

# Python 分析
import pandas as pd
df = pd.read_csv("WT001.csv")
df.plot(x='WMET_WSpeedNac', y='WTUR_TotPwrAt', kind='scatter')
```

## 授權

研究與教育用途。

## 相關文件

- `CLAUDE.md` — 詳細技術文件 (架構、API、物理模型參數)
- `TODO.md` — 開發路線圖、子模型替換指南、已知問題
- `docs/1040610-Z72_PLC_OPC_TAG_1040510.xlsx` — 原廠 Z72 OPC 標籤定義
