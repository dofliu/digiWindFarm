# TODO / Development Roadmap

## ✅ 已完成 (Phase 0-2)

### Phase 0: SCADA 數據模型
- [x] 40 個 SCADA 點位定義 (scada_registry.py)，對齊 Z72 原廠 OPC 標籤
- [x] i18n 多語言標籤 (en/zh-TW)
- [x] OPC Tag + Modbus Register 地址映射
- [x] TurbineReading 擴展到 51 欄位 (向下相容)

### Phase 1: 物理模型 + 故障 + 風況
- [x] 獨立物理模型 (simulator/physics/)，無 FastAPI 依賴
- [x] 完整耦合鏈：風速→轉速→功率→溫度→振動
- [x] 熱模型 (一階 RC)：發電機/變頻器/變壓器/機艙
- [x] 狀態機 TurState 1-9 (對齊 Bachmann)
- [x] 7 種故障場景，4 種劣化曲線 (linear/quadratic/exponential/logarithmic)
- [x] 告警碼系統 (A/T1/T2)，自動跳機
- [x] 9 種風況預設 + 自訂風速/風向/溫度/湍流
- [x] 可設定風機規格 (TurbineSpec): 切入/額定/切出、功率、葉輪直徑
- [x] 4 種預設機型 (Z72 5MW, Vestas V90 3MW, SG 8MW, Goldwind 2.5MW)
- [x] 限載功能 (curtailment): 全場 + 單機，pitch 自動調整
- [x] 操作控制: 停機/啟動/復位/定檢模式 (對齊 Modbus Coil)
- [x] 自訂功率曲線 (power curve lookup table)

### Phase 2: Modbus TCP + 通訊
- [x] pymodbus TCP Server (port 5020, 自動啟動)
- [x] 65 個 Holding Register，對齊原廠 Bachmann Excel
- [x] 14 slaves (每台風機一個 device ID)
- [x] 物理模型每秒更新 register
- [x] API 控制 (start/stop/status/registers)
- [x] 相容 pymodbus 3.5+ 和 3.12+

### 前端
- [x] 3 種儀表板模式 (卡片/摘要統計/列表)
- [x] 6 個 SCADA 子系統面板 (WGEN/WROT/WCNV/WNAC/WYAW/WGDC)
- [x] 多標籤即時趨勢圖 (6 預設 + 自訂標籤)
- [x] 故障注入控制台 (注入/監控/清除)
- [x] 操作控制面板 (停機/啟動/定檢/限載)
- [x] 風況控制 (9 預設 + 自訂)
- [x] 風機規格設定 (預設機型 + 自訂)
- [x] 中英文切換 (useI18n hook)
- [x] TurbineDetail 即時數據更新 (bug fix)
- [x] CSV 匯出 40 個獨立欄位

### 其他
- [x] OPC DA adapter TAG_MAPS 對齊 scada_registry
- [x] storage.py scada_json 欄位
- [x] CLAUDE.md 完整文件
- [x] Settings save 不再重置風況/控制設定

---

## 📋 待完成 (Phase 3-4)

### Phase 3: 維護工單 + 數據管理 (中優先級)
- [ ] 維護工單後端 CRUD API (目前 MaintenanceHub 使用前端 mock)
- [ ] SQLite 工單表 (work_orders)
- [ ] 故障事件 → 自動生成工單
- [ ] 數據保留策略 (定時清理過期 SQLite 數據)
- [ ] InfluxDB 時序資料庫整合 (可選，取代 SQLite)

### Phase 4: 部署 + 安全 (低優先級)
- [ ] JWT 認證 (保護敏感 API)
- [ ] Docker 容器化 (docker-compose 一鍵啟動)
- [ ] 前端生產構建 (FastAPI serve dist/)
- [ ] 環境變量管理 (.env)
- [ ] HTTPS / nginx 反向代理

---

## 🔮 未來可擴展

### 數據分析
- [ ] 功率曲線分析 (wind speed vs power scatter)
- [ ] 長期健康趨勢報告
- [ ] 故障預測 ML 模型整合
- [ ] 真實 SCADA CSV 匯入 (與 H127_Diagnosis 等專案聯動)

### 物理模型增強
- [ ] 更精確的功率曲線 (Cp-lambda-beta 3D 曲面)
- [ ] 尾流效應模型 (Jensen/Frandsen)
- [ ] 多點溫度模型 (6 點定子溫度)
- [ ] 葉片結冰模型
- [ ] 年度發電量預估 (AEP)

### 介面增強
- [ ] 風場鳥瞰圖 (2D/3D 風機位置)
- [ ] 歷史回放模式
- [ ] 自訂告警規則 (threshold 可設定)
- [ ] Email/LINE 通知
- [ ] 報表產生 (PDF)
- [ ] 行動裝置 PWA 支援

### 協定擴展
- [ ] OPC UA Server (取代 OPC DA)
- [ ] MQTT 支援
- [ ] IEC 61400-25 標準格式
- [ ] DNP3 / IEC 60870 整合

---

## 🐛 已知問題

1. **WorkOrderDetailModal.tsx** 有一個 TypeScript 類型錯誤 (Blob type mismatch)，不影響 build
2. **OPC DA adapter** 標籤映射已對齊但未在真實 OPC 伺服器上測試
3. **Gemini AI 診斷** 需要在 `frontend/.env.local` 設定 `GEMINI_API_KEY`
4. **歷史數據無限增長** — 尚未實作自動清理
5. **Modbus register** 部分大數值 (功率 >32767) 需使用低/高 16 位元拆分讀取

---

## 開發紀錄

| 日期 | 版本 | 內容 |
|------|------|------|
| 2026-04-03 | v0.1 | 初始架構 + CLAUDE.md |
| 2026-04-03 | v0.2 | 物理模型 40 SCADA tags + 故障引擎 + i18n |
| 2026-04-03 | v0.3 | 前端 SCADA 面板 + 故障注入 UI |
| 2026-04-03 | v0.4 | 風況控制 (9 預設 + 自訂) |
| 2026-04-03 | v0.5 | Modbus TCP 模擬器 (auto-start) |
| 2026-04-03 | v0.6 | 趨勢圖 + CSV 匯出增強 |
| 2026-04-03 | v0.7 | 風機規格設定 + 限載 |
| 2026-04-03 | v0.8 | 操作控制 (停機/啟動/定檢) |
| 2026-04-03 | v0.9 | 3 種儀表板模式 + 即時更新修復 |
