# 專案文件：智慧型風場營運管理系統 (Intelligent Wind Farm SCADA & Maintenance System)

本文檔旨在提供「智慧型風場營運管理系統」的全面概覽，整合即時監控、維護管理與數據分析功能。內容涵蓋專案目標、技術架構、功能模組及未來開發藍圖，以利團隊協作與進度追蹤。

---

## 1. 專案概述 (Project Overview)

本專案是一個整合性的 Web 應用程式，旨在為現代風力發電場提供一個從即時監控到維護派工、再到數據分析的中央管理平台。

- **目標使用者**: SCADA 控制室操作員、現場維修技師、場區主管、風場經理。
- **核心價值**: 透過數位化與智慧化工具，整合即時監控、維修工作流程與數據分析，以提升營運效率、降低停機時間，並為預測性維護奠定基礎。
- **主要功能**:
    1.  **即時監控儀表板 (SCADA Dashboard)**: 全場風機狀態、發電量總覽、單一風機詳細參數與歷史趨勢圖。
    2.  **AI 故障診斷 (AI Fault Diagnosis)**: 運用 Gemini API 分析異常數據，提供可能的故障原因與維修建議。
    3.  **維護管理中心 (Maintenance Hub)**: 工單管理、技師排班與派遣、維修紀錄（包含SOP檢查清單、照片、備註）。
    4.  **歷史數據與報表 (Historical Data & Reporting)**: 查詢歷史運轉數據、生成維修與效能報表。

---

## 2. 技術棧 (Tech Stack)

- **前端框架:** React 19
- **語言:** TypeScript
- **樣式:** Tailwind CSS
- **AI 模型:** Google Gemini API (`@google/genai`)
- **圖表:** Recharts
- **狀態管理:** React Hooks (useState, useMemo, useCallback) & Context API (未來規劃)
- **模組系統:** 原生 ES Modules 搭配 Import Maps
- **API 層:** 目前使用位於 `src/hooks` 的模擬數據 Hooks，未來將整合後端 API。

---

## 3. 專案結構 (Project Structure)

專案遵循功能導向的模組化結構，易於維護與擴展。

```
/
├── components/         # React 組件 (UI 模組)
├── hooks/              # 自定義 Hooks (主要為模擬數據邏輯)
├── services/           # 服務層 (外部通訊, 如 Gemini API)
├── types.ts            # 全域 TypeScript 型別定義
├── App.tsx             # 應用程式主入口與視圖邏輯
├── index.tsx           # React 應用程式掛載點
└── index.html          # 主 HTML 檔案
```

---

## 4. 核心功能模組說明 (Core Feature Modules)

### SCADA 儀表板
- **描述**: 提供風場的鳥瞰視圖與單機的微觀數據。`FarmOverview` 組件展示所有風機的關鍵狀態，而 `TurbineDetail` 則深入顯示單一風機的詳細運轉參數、歷史趨勢與儀表盤。
- **相關檔案**: `components/FarmOverview.tsx`, `components/TurbineDetail.tsx`, `components/Gauge.tsx`, `components/MiniTrendChart.tsx`

### AI 故障診斷
- **描述**: 當風機進入故障狀態時，系統可呼叫 `geminiService`，將當前的感測器數據傳送至 Gemini API。API 回傳結構化的診斷報告，包含可能原因與建議處理步驟，直接顯示在 `TurbineDetail` 頁面中，作為派遣決策的依據。
- **相關檔案**: `services/geminiService.ts`, `components/TurbineDetail.tsx`

### 維護中心
- **描述**: 此模組為維護作業的管理核心。`MaintenanceHub` 提供工單列表與技師名冊的切換視圖。`DispatchModal` 用於根據 AI 分析結果建立新工單並指派技師。`WorkOrderDetailModal` 則用於追蹤與完成維修任務，包含記錄備註與上傳照片。
- **相關檔案**: `components/MaintenanceHub.tsx`, `components/DispatchModal.tsx`, `components/WorkOrderDetailModal.tsx`, `hooks/useMockMaintenanceData.ts`

---

## 5. 當前已完成功能 (Current Features)

- [x] **即時 SCADA 監控**:
    - [x] 風場概覽，以卡片形式呈現每台風機的即時狀態與發電量。
    - [x] 詳細風機數據頁面，包含功率、轉速、風速等儀表板與即時趨勢圖。
- [x] **AI 故障診斷**:
    - [x] 當風機處於故障狀態時，可觸發 Gemini API 進行數據分析並提供診斷報告。
- [x] **基礎維護管理**:
    - [x] 技師名冊與狀態管理（執勤中、休息中、已派遣）。
    - [x] 從故障風機頁面直接建立工單並派遣技師。
    - [x] 查看工單列表與基本資訊。
    - [x] 填寫維修工單，包含文字備註與上傳現場照片。
    - [x] 完成工單並自動更新風機與技師狀態。
- [x] **響應式設計**: 介面能適應桌面與行動裝置。

---

## 6. 未來規劃與進度追蹤 (Roadmap & Progress Tracking)

此藍圖用於追蹤後續開發的優先級與進度。

### Phase 1: 核心功能整合與強化 (Core Feature Integration & Enhancement)
- [ ] **歷史數據查詢頁面**: 新增一個專門的視圖，允許使用者依時間範圍查詢特定風機的歷史參數，並以圖表和表格呈現。
- [ ] **強化維修報告**:
    - [ ] 在 `WorkOrderDetailModal` 中加入「標準檢查清單 (SOP Checklist)」，可根據故障類型動態載入。
    - [ ] 新增「耗材/零件更換」記錄功能，可動態增刪品項與數量。
- [ ] **表單草稿功能**: 在 `WorkOrderDetailModal` 中，自動將未儲存的 `notes` 和 `photos` 暫存於 LocalStorage，防止資料遺失。
- [ ] **搜尋與篩選**: 在「維護中心」的工單列表頁面，提供基於風機名稱、技師、狀態或日期的篩選功能。

### Phase 2: 後端整合與離線支援 (Backend Integration & Offline Support)
- [ ] **API 串接**: 將 `useMockTurbineData` 和 `useMockMaintenanceData` Hooks 中的模擬數據邏輯，替換為對真實後端 API 的呼叫。
- [ ] **真實使用者驗證**: 導入 JWT 或其他驗證機制，建立完整的登入/登出流程。
- [ ] **圖片儲存**: 將維修照片上傳至雲端儲存體 (例如: AWS S3, Google Cloud Storage)。
- [ ] **離線支援 (Offline First)**: 利用 Service Worker 和 IndexedDB，讓技師在無網路環境下仍可查看工單並填寫維修報告，待連線後自動同步。

### Phase 3: 主管與管理功能 (Supervisor & Admin Features)
- [ ] **管理儀表板 (Management Dashboard)**: 開發一個新的視圖，供主管查看關鍵績效指標 (KPIs)，如：設備可用率 (Availability)、平均修復時間 (MTTR)、各故障類型佔比等。
- [ ] **報表生成**: 提供將單筆維修紀錄或特定時間範圍的營運數據匯出為 PDF 或 CSV 格式的功能。
- [ ] **工單審核流程**: 主管可以審核技師提交的已完成工單，並可批准或提出意見退回修改。
- [ ] **權限管理**: (需後端支援) 建立角色與權限系統，區分操作員、技師、主管的不同權限。

### Phase 4: Gemini API 智慧功能深化 (Advanced AI Integration)
- [ ] **智慧填寫建議**: 當技師填寫「維修措施」時，利用 Gemini API 根據故障描述與歷史相似案例，提供標準化的文字建議。
- [ ] **維修照片分析**: 上傳維修前後照片時，可呼叫 Gemini Vision Pro 模型，自動辨識零件損壞情況或比對 SOP，確認維修品質。
- [ ] **語音轉文字輸入**: 整合瀏覽器 Web Speech API，讓技師能用口述方式記錄維修過程，即時轉為文字填入表單，解放雙手。
- [ ] **預測性維護建議**: 結合歷史數據與 Gemini 分析能力，在儀表板上主動提示可能即將發生故障的風機及其潛在原因。