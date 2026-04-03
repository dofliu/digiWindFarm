# 風力機監控系統 (Wind Turbine Monitoring System)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-v18+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-v18+-blue.svg)](https://reactjs.org/)

> 一個基於 OPC DA 通訊協議的即時風力機監控系統，提供網頁介面進行資料視覺化和查詢分析。

## 🌟 功能特色

- ⚡ **即時監控**: 透過 OPC DA 協議即時擷取風場資料
- 📊 **資料視覺化**: 豐富的圖表和儀表板顯示
- 🔍 **多樣化查詢**: 靈活的歷史資料查詢和分析
- 🚨 **告警系統**: 可配置的告警規則和多通道通知
- 📱 **響應式設計**: 支援桌面和行動裝置
- 🗄️ **資料管理**: 完整的資料儲存和歸檔機制

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────┐    ┌─────────────┐
│  風場控制器      │◄──►│ OPC Server  │◄──►│  後端服務    │
└─────────────────┘    └─────────────┘    └─────────────┘
                                                  │
                                          ┌─────────────┐
                                          │   資料庫     │
                                          └─────────────┘
                                                  │
                                          ┌─────────────┐
                                          │  網頁前端    │
                                          └─────────────┘
```

## 🚀 快速開始

### 前置需求

- Node.js 18.0+
- PostgreSQL 13+
- Redis 6+
- OPC Server (KEPServerEX 或相容軟體)

### 安裝步驟

1. **複製專案**
   ```bash
   git clone https://github.com/your-org/wind-turbine-monitoring.git
   cd wind-turbine-monitoring
   ```

2. **安裝相依套件**
   ```bash
   # 後端
   cd backend
   npm install
   
   # 前端
   cd ../frontend
   npm install
   ```

3. **環境設定**
   ```bash
   # 複製環境變數檔案
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # 編輯設定檔
   nano backend/.env
   ```

4. **資料庫設定**
   ```bash
   # 建立資料庫
   createdb wind_turbine_monitoring
   
   # 執行資料庫遷移
   cd backend
   npm run migrate
   ```

5. **啟動服務**
   ```bash
   # 使用 Docker Compose (推薦)
   docker-compose up -d
   
   # 或個別啟動
   # 後端
   cd backend && npm run dev
   
   # 前端
   cd frontend && npm start
   ```

### 使用 Docker

```bash
# 建置並啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

## 📁 專案結構

```
wind-turbine-monitoring/
├── backend/                 # 後端 API 服務
│   ├── src/
│   │   ├── controllers/     # 控制器
│   │   ├── models/         # 資料模型
│   │   ├── services/       # 業務邏輯
│   │   ├── utils/          # 工具函式
│   │   └── opc/           # OPC 通訊模組
│   ├── migrations/         # 資料庫遷移
│   └── tests/             # 測試檔案
├── frontend/               # 前端 React 應用
│   ├── src/
│   │   ├── components/     # 元件
│   │   ├── pages/         # 頁面
│   │   ├── hooks/         # React Hooks
│   │   ├── services/      # API 服務
│   │   └── utils/         # 工具函式
│   └── public/            # 靜態檔案
├── docs/                  # 專案文件
├── docker/               # Docker 設定
├── scripts/              # 部署腳本
└── monitoring/           # 監控設定 (Prometheus, Grafana)
```

## ⚙️ 設定說明

### 後端環境變數

```env
# 資料庫設定
DATABASE_URL=postgresql://user:password@localhost:5432/wind_turbine_monitoring

# Redis 設定
REDIS_URL=redis://localhost:6379

# OPC 設定
OPC_SERVER_HOST=localhost
OPC_SERVER_PORT=7890
OPC_UPDATE_RATE=1000

# JWT 設定
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRES_IN=7d

# 告警設定
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
```

### 前端環境變數

```env
# API 端點
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_WS_URL=ws://localhost:3001

# 地圖 API Key
REACT_APP_GOOGLE_MAPS_KEY=your_google_maps_api_key
```

## 📊 監控參數

系統監控以下風力機參數：

| 參數類別 | 參數名稱 | 單位 | 描述 |
|---------|---------|------|------|
| 風況 | 風速 | m/s | 即時風速 |
| 風況 | 風向 | 度 | 風向角度 |
| 電力 | 發電功率 | kW | 即時發電功率 |
| 電力 | 電壓 | V | 輸出電壓 |
| 電力 | 電流 | A | 輸出電流 |
| 機械 | 轉速 | rpm | 轉子轉速 |
| 機械 | 偏航角度 | 度 | 機艙偏航角度 |
| 溫度 | 機艙溫度 | °C | 機艙內部溫度 |
| 溫度 | 軸承溫度 | °C | 主軸承溫度 |
| 狀態 | 運行狀態 | - | 設備運行狀態 |

## 🔌 API 文件

### 認證
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

### 風力機資料
```http
# 取得所有風力機
GET /api/turbines

# 取得特定風力機即時資料
GET /api/turbines/{id}/realtime

# 取得歷史資料
GET /api/turbines/{id}/history?start=2024-01-01&end=2024-01-31&interval=1h
```

### WebSocket 連線
```javascript
const ws = new WebSocket('ws://localhost:3001');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('即時資料:', data);
};
```

## 🧪 測試

```bash
# 後端測試
cd backend
npm test

# 前端測試
cd frontend
npm test

# E2E 測試
npm run test:e2e
```

## 📦 部署

### 開發環境
```bash
# 啟動開發伺服器
npm run dev
```

### 生產環境
```bash
# 建置應用程式
npm run build

# 啟動生產伺服器
npm run start:prod
```

### Docker 部署
```bash
# 建置映像檔
docker build -t wind-turbine-monitoring .

# 執行容器
docker run -p 3000:3000 wind-turbine-monitoring
```

## 📋 故障排除

### 常見問題

**Q: OPC 連線失敗**
```
A: 檢查 OPC Server 是否正常運行，確認 CLSID 和連線參數正確
```

**Q: 資料庫連線失敗**
```
A: 檢查 PostgreSQL 服務狀態和連線字串設定
```

**Q: 前端無法連線到後端 API**
```
A: 檢查 CORS 設定和 API 端點網址
```

### 日誌查看

```bash
# 後端日誌
docker-compose logs -f backend

# 前端日誌
docker-compose logs -f frontend

# 資料庫日誌
docker-compose logs -f postgres
```

## 🤝 貢獻指南

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 👥 專案團隊

- **專案負責人**: [Your Name](mailto:your.email@example.com)
- **後端開發**: [Backend Developer](mailto:backend@example.com)  
- **前端開發**: [Frontend Developer](mailto:frontend@example.com)
- **DevOps**: [DevOps Engineer](mailto:devops@example.com)

## 📞 支援與聯絡

- 📧 Email: support@yourcompany.com
- 📱 電話: +886-2-1234-5678
- 🌐 網站: https://yourcompany.com

---

⭐ 如果這個專案對你有幫助，請給我們一個 Star！