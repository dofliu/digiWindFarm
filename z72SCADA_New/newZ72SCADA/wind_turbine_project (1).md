# 風力機監控系統 (Wind Turbine Monitoring System)

## 專案概述

本專案旨在開發一個即時風力機監控系統，透過 OPC 通訊協議從風場硬體控制器擷取即時資料，並提供網頁介面進行資料視覺化和查詢分析。

## 系統架構

```
風場硬體控制器 ←→ OPC Server ←→ 後端服務 ←→ 資料庫
                                    ↕
                               網頁前端介面
```

### 技術棧

**後端**
- Node.js / Python (FastAPI)
- OPC Client Library (node-opcda / OpenOPC)
- 資料庫: PostgreSQL / MongoDB
- API: RESTful / GraphQL

**前端**
- React / Vue.js
- 圖表庫: Chart.js / D3.js / ECharts
- 即時通訊: WebSocket / Server-Sent Events

**基礎設施**
- Docker 容器化
- Nginx 反向代理
- Redis 快取

## 功能規格

### 核心功能

1. **即時資料擷取**
   - 透過 OPC DA 通訊協議連接風場控制器
   - 支援多台風力機同時監控
   - 可配置資料採樣頻率

2. **資料儲存與管理**
   - 時間序列資料儲存
   - 歷史資料歸檔
   - 資料備份與恢復

3. **網頁監控介面**
   - 即時儀表板顯示
   - 歷史趨勢圖表
   - 告警通知系統
   - 多樣化資料查詢

4. **告警系統**
   - 可配置告警規則
   - 多通道通知 (Email, SMS, 推播)
   - 告警歷史記錄

### 監控參數

- 風速、風向
- 發電功率、電壓、電流
- 機艙溫度、軸承溫度
- 葉片角度、偏航角度
- 振動數據
- 運行狀態、故障碼

## 系統需求

### 硬體需求
- 支援 OPC DA 的風場控制器
- 伺服器: CPU 4核心, RAM 8GB, 儲存 500GB
- 網路: 穩定的區域網路連線

### 軟體需求
- Windows Server / Linux (支援 OPC)
- 資料庫管理系統
- Web 伺服器
- OPC Server 軟體

## 資料庫設計

### 主要資料表

```sql
-- 風力機基本資料
CREATE TABLE wind_turbines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(50),
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    installation_date DATE,
    status VARCHAR(20) DEFAULT 'active'
);

-- 即時監控資料
CREATE TABLE realtime_data (
    id SERIAL PRIMARY KEY,
    turbine_id INTEGER REFERENCES wind_turbines(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wind_speed DECIMAL(5,2),
    wind_direction INTEGER,
    power_output DECIMAL(8,2),
    rotor_rpm DECIMAL(6,2),
    nacelle_temperature DECIMAL(4,1),
    status_code INTEGER
);

-- 告警記錄
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    turbine_id INTEGER REFERENCES wind_turbines(id),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE
);
```

## API 設計

### RESTful API 端點

```
GET /api/turbines              # 取得所有風力機清單
GET /api/turbines/{id}         # 取得特定風力機資訊
GET /api/turbines/{id}/data    # 取得即時資料
GET /api/turbines/{id}/history # 取得歷史資料
GET /api/alerts               # 取得告警清單
POST /api/alerts/{id}/ack     # 確認告警
```

### WebSocket 事件

```javascript
// 即時資料推送
{
  "type": "realtime_data",
  "turbine_id": 1,
  "data": {
    "wind_speed": 12.5,
    "power_output": 1850.2,
    "timestamp": "2024-12-19T10:30:00Z"
  }
}

// 告警通知
{
  "type": "alert",
  "turbine_id": 1,
  "severity": "high",
  "message": "風速超過安全限制"
}
```

## 安全性考量

- OPC 通訊加密
- API 存取權限控制
- 資料傳輸 HTTPS
- 使用者身份驗證
- 操作日誌記錄

## 部署架構

### Development
```
Docker Compose:
- API Server
- Database
- Redis
- Frontend Dev Server
```

### Production
```
Kubernetes / Docker Swarm:
- Load Balancer (Nginx)
- API Server (多實例)
- Database Cluster
- Monitoring (Prometheus + Grafana)
```

## 專案時程

### Phase 1 (4週) - 基礎架構
- OPC 通訊模組開發
- 資料庫設計與建置
- 基礎 API 開發

### Phase 2 (4週) - 前端開發
- 網頁介面設計
- 即時資料顯示
- 基本查詢功能

### Phase 3 (3週) - 進階功能
- 告警系統
- 歷史資料分析
- 報表生成

### Phase 4 (2週) - 測試與部署
- 系統測試
- 效能優化
- 正式部署

## 風險評估

1. **OPC 通訊穩定性** - 需要處理網路中斷和重連機制
2. **資料量增長** - 需要考慮資料歸檔和清理策略
3. **即時性要求** - 需要優化資料處理和傳輸效率
4. **硬體相容性** - 不同廠牌控制器的 OPC 實作差異

## 維護計畫

- 定期資料庫備份
- 系統效能監控
- 安全性更新
- 功能擴展規劃

---

**專案負責人**: [待指定]  
**最後更新**: 2024-12-19  
**版本**: v1.0