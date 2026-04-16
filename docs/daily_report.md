# digiWindFarm Daily Report

> 最後更新：2026-04-16

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/happy-goodall-dfqED`）：
- [8d91f0a] feat: add bearing defect frequency model (BPFO/BPFI) for condition monitoring (#58)

過去 24 小時 main 分支合併：
- [fbcd68a] Merge pull request #64 from dofliu/claude/happy-goodall-ek3dv（塔架 SDOF 動態響應）
- [029b929] Merge pull request #63 from dofliu/claude/happy-goodall-sfnpJ（Cp 氣動模型 + docstrings）
- [076073e] Merge pull request #60 from dofliu/claude/awesome-albattani-IzD2C
- [096f924] Merge pull request #59 from dofliu/claude/awesome-albattani-o49ay
- [d2a5c1f] Merge pull request #56 from dofliu/claude/determined-goldberg-f1OFZ
- [7220898] Merge pull request #55 from dofliu/claude/gracious-mccarthy-j7IiT
- [e658f75] Merge pull request #54 from dofliu/claude/gracious-mccarthy-MNcvo

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #62 | 塔架前後動態響應 — 自然頻率振盪模擬 | PR #64 已合併至 main，SDOF 一階模態完成 |
| 進展 | #58 | 頻譜振動警報閾值與邊帶分析 | 新增 BPFO/BPFI 軸承缺陷頻率計算模型，已推送 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，剩前端 RUL 視覺化 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求，待規劃 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求，待規劃 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 漏洞數量不變，尚未升級 |
| 保持 | #45 | 108 個公開函數缺少 docstring | 累計修復 102 個，剩餘 6 個 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 錯誤數維持 115 個，核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker Compose 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | BPFO/BPFI 已實作，邊帶分析待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 後端完成，前端待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #45 | 108 個公開函數缺少 docstring | documentation, auto-detected | 2026-04-13 | 已修 102 個，剩 6 個 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 降至 115 個，核心模組已清零 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-16 | 0 | 無測試套件 | 疲勞警報事件偵測邏輯已完成 |
| `server/routers/` | 2026-04-16 | 0 | 無測試套件 | 8 個 router 全部有 docstring |
| `simulator/` | 2026-04-16 | 0 | 無測試套件 | engine time_scale setter 已補 docstring |
| `simulator/physics/` | 2026-04-16 | 0 | 無測試套件 | 新增 BPFO/BPFI 軸承缺陷頻率模型 |
| `frontend/` | 2026-04-15 | 0 | 無測試套件 | RUL 視覺化待實作 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案（dashboard.py 等） |

## API Endpoints

| Method | Path | 狀態 | 文件同步 |
|--------|------|------|----------|
| GET | /api/health | 正常 | ✅ |
| GET | /api/turbines | 正常 | ✅ |
| GET | /api/turbines/{id} | 正常 | ✅ |
| GET | /api/turbines/{id}/history | 正常 | ✅ |
| GET | /api/turbines/{id}/trend | 正常 | ✅ |
| GET | /api/turbines/farm-status | 正常 | ✅ |
| GET | /api/turbines/farm-trend | 正常 | ✅ |
| GET | /api/config | 正常 | ✅ |
| POST | /api/config/datasource | 正常 | ✅ |
| POST | /api/config/simulation | 正常 | ✅ |
| GET | /api/config/wind | 正常 | ✅ |
| POST | /api/config/wind | 正常 | ✅ |
| POST | /api/config/wind/clear | 正常 | ✅ |
| GET | /api/config/simulation/time-scale | 正常 | ✅ |
| POST | /api/config/simulation/time-scale | 正常 | ✅ |
| POST | /api/config/simulation/generate-bulk | 正常 | ✅ |
| GET | /api/config/grid | 正常 | ✅ |
| POST | /api/config/grid | 正常 | ✅ |
| POST | /api/config/grid/clear | 正常 | ✅ |
| GET | /api/config/storage/stats | 正常 | ✅ |
| GET | /api/config/sessions | 正常 | ✅ |
| POST | /api/config/storage/maintenance | 正常 | ✅ |
| GET | /api/config/turbine-spec | 正常 | ✅ |
| POST | /api/config/turbine-spec | 正常 | ✅ |
| GET | /api/config/turbine-spec/presets | 正常 | ✅ |
| POST | /api/control/command | 正常 | ✅ |
| POST | /api/control/curtail | 正常 | ✅ |
| GET | /api/control/{id}/status | 正常 | ✅ |
| GET | /api/faults/scenarios | 正常 | ✅ |
| POST | /api/faults/inject | 正常 | ✅ |
| GET | /api/faults/active | 正常 | ✅ |
| POST | /api/faults/clear | 正常 | ✅ |
| GET | /api/faults/test-plans | 正常 | ✅ |
| POST | /api/faults/test-plans/{plan_id}/run | 正常 | ✅ |
| GET | /api/maintenance/work-orders | 正常 | ✅ |
| POST | /api/maintenance/work-orders | 正常 | ✅ |
| GET | /api/maintenance/work-orders/{id} | 正常 | ✅ |
| PATCH | /api/maintenance/work-orders/{id} | 正常 | ✅ |
| GET | /api/maintenance/technicians | 正常 | ✅ |
| POST | /api/maintenance/technicians | 正常 | ✅ |
| PATCH | /api/maintenance/technicians/{id}/status | 正常 | ✅ |
| GET | /api/maintenance/events/compare | 正常 | ✅ |
| GET | /api/i18n/tags | 正常 | ✅ |
| GET | /api/i18n/tags/all | 正常 | ✅ |
| GET | /api/i18n/tags/registry | 正常 | ✅ |
| GET | /api/modbus/status | 正常 | ✅ |
| POST | /api/modbus/start | 正常 | ✅ |
| POST | /api/modbus/stop | 正常 | ✅ |
| GET | /api/modbus/registers | 正常 | ✅ |
| GET | /api/export/snapshot | 正常 | ✅ |
| GET | /api/export/history | 正常 | ✅ |
| GET | /api/export/events | 正常 | ✅ |
| WS | /ws/realtime | 正常 | ✅ |

共 54 個路由（53 HTTP + 1 WebSocket），全部與文件同步。

## 程式碼品質

- Lint 錯誤：115（核心模組 server/ + simulator/ 維持 0 錯誤，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- 無 docstring 的公開函數：6 個（與上次相同）
  - 根目錄原型：dashboard.py `update_charts()`、wind_model.py `get_status()`/`get_wind_direction()`/`get_ambient_temp()`
  - 內部輔助：storage.py `to_float()` x2（巢狀函數，非模組級公開）
- Broken imports：0（核心模組）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：84 個（新增 4 個 BPFO/BPFI 標籤，原 80 個）

## 今日新增功能

### 軸承缺陷頻率模型 — BPFO/BPFI（#58）
- **物理原理**：滾動軸承缺陷會在特定頻率產生衝擊振動，BPFO（外環）和 BPFI（內環）頻率由軸承幾何決定
- **實作方式**：
  1. `vibration_spectral.py`：新增軸承幾何參數（滾動體數量 n=23、直徑比 d/D=0.18、接觸角 10°）
  2. BPFO = (n/2) x f_shaft x (1 - d/D x cos α)
  3. BPFI = (n/2) x f_shaft x (1 + d/D x cos α)
  4. 健康軸承：BPFO/BPFI 振幅極低（~0.005 mm/s）
  5. bearing_wear 故障：振幅隨嚴重度增長（BPFO +0.25, BPFI +0.15 mm/s x severity）
  6. 每台風機 ±3% 幾何差異（模擬製造公差）
- **新增 SCADA 標籤**：
  - `WVIB_BpfoFreq`：外環缺陷頻率（Hz）
  - `WVIB_BpfiFreq`：內環缺陷頻率（Hz）
  - `WVIB_BpfoAmp`：外環缺陷振幅（mm/s）
  - `WVIB_BpfiAmp`：內環缺陷振幅（mm/s）
- **預期效果**：
  - 正常運轉時 BPFO ~3.4 Hz、BPFI ~4.9 Hz（在額定轉速 ~22 RPM 下）
  - 注入 bearing_wear 故障後，BPFO/BPFI 振幅明顯上升
  - 可作為狀態監測系統的早期缺陷指標
- **驗證方式**：注入 bearing_wear 故障後，觀察歷史趨勢圖中 BPFO/BPFI 振幅變化

## 建議行動

1. **合併 BPFO/BPFI 模型**：已推送至 `claude/happy-goodall-dfqED`，可建立 PR 合併
2. **實作 #58 齒輪嚙合邊帶分析**：齒輪嚙合頻率周圍的調變邊帶（sideband）模擬
3. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
4. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
5. **完善 #57 前端視覺化**：前端新增 RUL 顯示和疲勞警報等級視覺化
6. **驗證模擬品質**：啟動模擬，使用 `data_quality_analysis.py` 驗證 BPFO/BPFI 輸出
