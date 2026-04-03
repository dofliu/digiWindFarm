# 風力機監控系統 - 快速安裝部署指引

## 🚀 一鍵安裝腳本

### 1. 環境變數設定檔

建立 `backend/.env` 檔案：
```env
# 資料庫設定
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wind_farm_monitoring
DB_USER=postgres
DB_PASSWORD=your_password

# Redis 設定
REDIS_URL=redis://localhost:6379

# JWT 設定
JWT_SECRET=your_super_secret_jwt_key_here
JWT_EXPIRES_IN=7d

# OPC 設定 (根據你的實際環境調整)
OPC_SERVER_HOST=192.168.1.100
OPC_SERVER_CLSID={F8582CF2-88FB-11D0-B850-00C0F0104305}
OPC_PROG_ID=KEPware.KEPServerEx.V6
OPC_UPDATE_RATE=1000

# 前端網址
FRONTEND_URL=http://localhost:3000

# 伺服器設定
PORT=3001
NODE_ENV=development
```

### 2. Docker Compose 一鍵部署

建立 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  # PostgreSQL 資料庫
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: wind_farm_monitoring
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  # Redis 快取
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  # 後端 API
  backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=wind_farm_monitoring
      - DB_USER=postgres
      - DB_PASSWORD=password123
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=your_super_secret_jwt_key_here
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - /app/node_modules
    restart: unless-stopped

  # 前端應用
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:3001/api
      - REACT_APP_WS_URL=ws://localhost:3001
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. 後端 Dockerfile

建立 `backend/Dockerfile`：
```dockerfile
FROM node:18-alpine

WORKDIR /app

# 複製 package.json 和安裝相依套件
COPY package*.json ./
RUN npm ci --only=production

# 複製原始碼
COPY . .

# 建立日誌目錄
RUN mkdir -p logs

EXPOSE 3001

CMD ["npm", "start"]
```

### 4. 前端 Dockerfile

建立 `frontend/Dockerfile`：
```dockerfile
FROM node:18-alpine

WORKDIR /app

# 複製 package.json 和安裝相依套件
COPY package*.json ./
RUN npm ci

# 複製原始碼
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

## 🔧 手動安裝步驟

### 步驟 1: 環境準備
```bash
# 確保已安裝 Node.js 18+ 和 PostgreSQL
node --version  # 應該是 v18+
psql --version  # 確認 PostgreSQL 已安裝

# 建立專案目錄
mkdir wind-farm-monitoring
cd wind-farm-monitoring
```

### 步驟 2: 後端設定
```bash
# 建立後端目錄和檔案
mkdir backend
cd backend

# 初始化 npm 和安裝套件
npm init -y
npm install express express-rate-limit helmet cors morgan dotenv jsonwebtoken bcryptjs sequelize pg redis socket.io node-opcda winston compression express-validator multer csv-writer node-cron

npm install --save-dev nodemon jest supertest

# 複製我提供的後端程式碼到 src/ 目錄
# 建立資料庫
createdb wind_farm_monitoring

# 執行資料庫遷移
npm run migrate
```

### 步驟 3: 前端設定
```bash
# 回到根目錄
cd ..

# 建立 React 應用
npx create-react-app frontend
cd frontend

# 安裝額外套件
npm install lucide-react chart.js react-chartjs-2 socket.io-client axios

# 替換 src/App.js 為我提供的程式碼
```

### 步驟 4: OPC 連線設定
```javascript
// 在 backend/config/turbines.js 建立風機配置
module.exports = [
  {
    id: 1,
    name: 'WT-01',
    latitude: 24.1569,
    longitude: 121.2421,
    opcConfig: {
      clsid: '{你的OPC_Server_CLSID}',
      host: '192.168.1.100', // 你的 PLC IP
      progId: 'KEPware.KEPServerEx.V6', // 根據你的 OPC Server
      baseTag: 'Channel1.Device1.WT01', // 根據你的標籤結構
      updateRate: 1000
    }
  },
  // ... 其他 13 台風機的設定
];
```

## ⚡ 一鍵啟動

### 使用 Docker (推薦)
```bash
# 複製所有檔案到伺服器後
docker-compose up -d

# 查看狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 手動啟動
```bash
# 終端機 1: 啟動後端
cd backend
npm run dev

# 終端機 2: 啟動前端
cd frontend
npm start

# 瀏覽器開啟 http://localhost:3000
```

## 🔧 OPC 連線設定

### 1. 確認你的 OPC Server 資訊
```bash
# 使用 OPC Expert 或類似工具確認：
# - CLSID (類別識別碼)
# - ProgID (程式識別碼) 
# - 標籤結構
# - 資料型態
```

### 2. 修改 OPC 設定檔
```javascript
// backend/config/opcConfig.js
const turbineConfigs = [
  {
    id: 1,
    name: 'WT-01',
    opcConfig: {
      host: '你的PLC_IP',
      clsid: '{你的OPC_Server_CLSID}',
      progId: '你的OPC_Server_ProgID',
      tags: {
        windSpeed: 'Channel1.Device1.WT01.WindSpeed',
        windDirection: 'Channel1.Device1.WT01.WindDirection',
        powerOutput: 'Channel1.Device1.WT01.PowerOutput',
        rotorRpm: 'Channel1.Device1.WT01.RotorRpm',
        // ... 其他標籤
      }
    }
  }
  // ... 其他風機配置
];
```

## 📊 資料庫初始化

```sql
-- 手動插入風機基本資料
INSERT INTO wind_turbines (name, model, capacity, latitude, longitude, installation_date, status) VALUES
('WT-01', 'Vestas V90-2.0', 2000, 24.1569, 121.2421, '2020-01-15', 'active'),
('WT-02', 'Vestas V90-2.0', 2000, 24.1580, 121.2435, '2020-01-16', 'active'),
-- ... 其他 12 台風機
;
```

## 🚨 常見問題解決

### OPC 連線問題
```bash
# 檢查 Windows 防火牆
# 確認 DCOM 設定
# 檢查 OPC Server 是否運行
# 確認網路連通性：ping PLC_IP
```

### 資料庫連線問題
```bash
# 檢查 PostgreSQL 服務
sudo systemctl status postgresql

# 檢查連線權限
psql -h localhost -U postgres -d wind_farm_monitoring
```

### 前端連線問題
```bash
# 檢查 CORS 設定
# 確認 API 端點正確
# 檢查防火牆設定
```

## 📱 行動裝置存取

系統已支援響應式設計，可直接在手機或平板上使用。

## 🔒 安全性設定

1. **修改預設密碼**
2. **設定 HTTPS** (生產環境)
3. **配置防火牆規則**
4. **定期更新套件**

## 📈 效能監控

```bash
# 安裝監控工具
docker-compose -f docker-compose.monitoring.yml up -d

# 存取 Grafana: http://localhost:3300
# 預設帳號: admin/admin
```

---

🎉 **安裝完成後，你將擁有：**
- 即時風機監控系統
- 地圖顯示 14 台風機
- 動畫顯示風機狀態
- 完整的告警系統
- 歷史資料查詢
- 資料匯出功能
- 自動備份機制

需要我協助任何安裝或設定問題，請隨時告訴我！