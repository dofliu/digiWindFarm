# 離岸風力發電場數位孿生系統開發專案

## 專案概述

### 專案名稱
離岸風力發電場數位孿生模擬系統 (Offshore Wind Farm Digital Twin Simulation System)

### 專案願景
建立一個基於物理模型的離岸風力發電場模擬系統，能夠真實反映風力發電機的運轉特性，並提供即時監控、資料分析與故障診斷功能。

### 專案目標
1. 開發具備真實物理模型的風力發電機模擬器
2. 實現 OPC UA 通訊協定的資料傳輸
3. 建立完整的 SCADA 監控系統
4. 提供資料儲存與歷史查詢功能
5. 支援故障模擬與診斷分析

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                     風力發電機模擬層                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │環境模型  │  │風機物理  │  │子系統模型│  │故障模擬  │   │
│  │(風速/風向)│  │  模型    │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  OPC UA   │
                    │  Server   │
                    └─────┬─────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
      ┌─────▼─────┐             ┌──────▼──────┐
      │   資料庫   │             │    SCADA    │
      │  (時序DB)  │◄────────────│  監控系統   │
      └───────────┘             └─────────────┘
```

## 技術架構

### 開發語言與框架
- **後端**: Python 3.10+
- **資料庫**: TimescaleDB (PostgreSQL 時序資料庫)
- **OPC UA**: python-opcua / asyncua
- **SCADA前端**: React + TypeScript
- **資料視覺化**: Grafana / Apache ECharts
- **訊息佇列**: Redis / RabbitMQ

### 系統需求
- Docker & Docker Compose
- Python 虛擬環境
- Node.js 18+
- PostgreSQL 14+

## 核心模組設計

### 1. 環境模型模組 (Environment Module)

#### 1.1 風速模型
```python
class WindModel:
    """
    風速模型：提供基於時間的風速變化
    """
    - base_wind_speed: 基礎風速
    - turbulence_intensity: 紊流強度
    - daily_pattern: 日變化模式
    - seasonal_variation: 季節變化
```

**初期實作**:
- 簡單的日變化模式：
  - 06:00 - 3 m/s
  - 12:00 - 7 m/s  
  - 18:00 - 10 m/s
  - 00:00 - 4 m/s
- 固定紊流強度：10%

### 2. 風力發電機物理模型 (Wind Turbine Physics)

#### 2.1 功率計算模型
```python
class PowerCalculation:
    """
    基於風能理論的功率計算
    P = 0.5 × ρ × A × V³ × Cp
    """
    - air_density: 空氣密度 (1.225 kg/m³)
    - rotor_area: 葉輪掃掠面積
    - wind_speed: 風速
    - power_coefficient: 功率係數 (Cp)
```

#### 2.2 功率曲線
```python
class PowerCurve:
    """
    風機功率曲線定義
    """
    - cut_in_speed: 啟動風速 (3 m/s)
    - rated_speed: 額定風速 (12 m/s)
    - cut_out_speed: 停機風速 (25 m/s)
    - rated_power: 額定功率 (例: 5 MW)
```

### 3. 子系統模型 (Subsystem Models)

#### 3.1 齒輪箱模型 (Gearbox)
```python
class GearboxModel:
    """
    齒輪箱模型
    """
    - gear_ratio: 增速比 (1:100)
    - efficiency: 傳動效率 (98%)
    - temperature: 運轉溫度
    - vibration: 振動數據
    - oil_pressure: 油壓
```

#### 3.2 發電機模型 (Generator)
```python
class GeneratorModel:
    """
    發電機模型
    """
    - generator_efficiency: 發電效率 (96%)
    - stator_temperature: 定子溫度
    - rotor_temperature: 轉子溫度
    - voltage: 輸出電壓
    - current: 輸出電流
    - power_factor: 功率因數
```

#### 3.3 變槳系統 (Pitch System)
```python
class PitchSystem:
    """
    變槳控制系統
    """
    - pitch_angle: 槳葉角度
    - pitch_rate: 變槳速率
    - hydraulic_pressure: 液壓壓力
    - pitch_motor_temperature: 變槳馬達溫度
```

#### 3.4 偏航系統 (Yaw System)
```python
class YawSystem:
    """
    偏航對風系統
    """
    - yaw_angle: 偏航角度
    - yaw_error: 對風誤差
    - yaw_motor_status: 偏航馬達狀態
```

### 4. 資料整合模組

#### 4.1 訊號管理器
```python
class SignalManager:
    """
    整合所有子系統訊號
    """
    - collect_signals(): 收集所有子系統資料
    - format_data(): 格式化資料
    - timestamp_data(): 加入時間戳記
```

## OPC UA 通訊實作

### OPC UA Server 設計
```python
class WindTurbineOPCServer:
    """
    OPC UA 伺服器實作
    """
    - server_endpoint: "opc.tcp://localhost:4840"
    - namespace: "WindTurbineSimulation"
    - update_frequency: 1 Hz
    
    節點結構:
    WindTurbine/
    ├── Environmental/
    │   ├── WindSpeed
    │   └── WindDirection
    ├── Performance/
    │   ├── Power
    │   ├── RotorSpeed
    │   └── PitchAngle
    └── Subsystems/
        ├── Gearbox/
        ├── Generator/
        └── PitchSystem/
```

## 資料庫設計

### 時序資料表結構

```sql
-- 風機運轉資料表
CREATE TABLE turbine_data (
    time TIMESTAMPTZ NOT NULL,
    turbine_id VARCHAR(50),
    wind_speed FLOAT,
    power_output FLOAT,
    rotor_speed FLOAT,
    pitch_angle FLOAT,
    gearbox_temp FLOAT,
    generator_temp FLOAT,
    -- 其他欄位...
    PRIMARY KEY (time, turbine_id)
);

-- 建立 hypertable (TimescaleDB)
SELECT create_hypertable('turbine_data', 'time');

-- 警報記錄表
CREATE TABLE alarms (
    alarm_id SERIAL PRIMARY KEY,
    turbine_id VARCHAR(50),
    alarm_time TIMESTAMPTZ,
    alarm_type VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);
```

## SCADA 監控系統

### 功能模組

#### 1. 即時監控儀表板
- 風機運轉狀態總覽
- 關鍵參數即時顯示
- 效能指標監控
- 警報狀態顯示

#### 2. 歷史資料查詢
- 時間範圍選擇
- 參數趨勢圖表
- 資料匯出功能
- 統計分析報表

#### 3. 警報管理系統
- 警報設定與觸發
- 警報等級分類
- 警報確認機制
- 警報歷史記錄

#### 4. 診斷分析工具
- 效能分析
- 故障診斷
- 預測性維護
- 趨勢分析

## 開發階段規劃

### 第一階段：基礎架構 (Week 1-2)
- [x] 專案架構設計
- [ ] 開發環境建置
- [ ] 基本風速模型實作
- [ ] 簡單功率計算

### 第二階段：單機模擬 (Week 3-4)
- [ ] 完整風機物理模型
- [ ] 子系統基礎模型
- [ ] 資料整合機制
- [ ] 模擬資料產生

### 第三階段：通訊整合 (Week 5-6)
- [ ] OPC UA Server 實作
- [ ] 資料格式定義
- [ ] 通訊測試
- [ ] 效能優化

### 第四階段：資料儲存 (Week 7-8)
- [ ] 資料庫架構建立
- [ ] 資料寫入服務
- [ ] 資料查詢 API
- [ ] 備份機制

### 第五階段：SCADA 開發 (Week 9-11)
- [ ] 前端框架建立
- [ ] 即時監控介面
- [ ] 歷史查詢功能
- [ ] 警報系統

### 第六階段：進階功能 (Week 12-14)
- [ ] 故障模擬機制
- [ ] 診斷分析工具
- [ ] 效能優化
- [ ] 系統測試

### 第七階段：部署與文件 (Week 15-16)
- [ ] Docker 容器化
- [ ] 部署文件
- [ ] 使用手冊
- [ ] API 文件

## 專案目錄結構

```
wind-turbine-simulation/
├── docker-compose.yml
├── requirements.txt
├── README.md
├── .env.example
│
├── simulator/                 # 模擬器核心
│   ├── __init__.py
│   ├── models/               # 物理模型
│   │   ├── wind_model.py
│   │   ├── turbine.py
│   │   ├── gearbox.py
│   │   ├── generator.py
│   │   └── pitch_system.py
│   ├── core/                 # 核心功能
│   │   ├── physics.py
│   │   ├── signal_manager.py
│   │   └── fault_simulator.py
│   └── config/
│       └── turbine_config.yaml
│
├── opcua/                    # OPC UA 服務
│   ├── __init__.py
│   ├── server.py
│   └── node_manager.py
│
├── database/                 # 資料庫服務
│   ├── __init__.py
│   ├── models.py
│   ├── connection.py
│   └── migrations/
│
├── scada/                    # SCADA 系統
│   ├── backend/
│   │   ├── api/
│   │   ├── services/
│   │   └── utils/
│   └── frontend/
│       ├── src/
│       ├── public/
│       └── package.json
│
├── tests/                    # 測試
│   ├── unit/
│   ├── integration/
│   └── performance/
│
└── docs/                     # 文件
    ├── API.md
    ├── DEPLOYMENT.md
    └── USER_GUIDE.md
```

## 開發規範

### 程式碼規範
- 遵循 PEP 8 (Python)
- 使用 TypeScript ESLint 規則
- 完整的型別標註
- 單元測試覆蓋率 > 80%

### Git 工作流程
- 主分支：main
- 開發分支：develop
- 功能分支：feature/功能名稱
- 修復分支：hotfix/問題描述

### 提交訊息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

## 部署需求

### 硬體需求
- CPU: 4 cores 以上
- RAM: 8 GB 以上
- Storage: 50 GB SSD
- Network: 1 Gbps

### 軟體需求
- Ubuntu 20.04 LTS 或更新版本
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+
- Redis 6+

## 授權與維護

### 授權
MIT License

### 維護團隊
- 專案負責人
- 後端開發工程師
- 前端開發工程師
- 資料庫管理員
- 測試工程師

### 聯絡方式
- Email: project@example.com
- Issue Tracker: GitHub Issues

---

**文件版本**: 1.0.0  
**最後更新**: 2025-10-27  
**狀態**: 開發中