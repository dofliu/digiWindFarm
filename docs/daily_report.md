# digiWindFarm Daily Report

> 最後更新：2026-04-16

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/happy-goodall-Mov9d`）：
- [3a19dc8] feat: add gear mesh sideband analysis model for gearbox condition monitoring (#58)

過去 24 小時 main 分支合併：
- [0e0e409] Merge pull request #65（BPFO/BPFI 軸承缺陷頻率模型）
- [fbcd68a] Merge pull request #64（塔架 SDOF 動態響應）
- [029b929] Merge pull request #63（Cp 氣動模型 + docstrings）
- [076073e] Merge pull request #60
- [096f924] Merge pull request #59
- [d2a5c1f] Merge pull request #56
- [7220898] Merge pull request #55
- [e658f75] Merge pull request #54

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #45 | 108 個公開函數缺少 docstring | 核心模組全數補齊，剩 6 個非關鍵（巢狀函數+原型檔案），已完成 |
| 進展 | #58 | 頻譜振動警報閾值與邊帶分析 | 新增齒輪嚙合邊帶（sideband）分析模型，已推送 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，剩前端 RUL 視覺化 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求，待規劃 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求，待規劃 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 漏洞數量不變，尚未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 維持 115 個，核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker Compose 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | BPFO/BPFI + 邊帶分析已實作，頻帶警報閾值曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 後端完成，前端待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 降至 115 個，核心模組已清零 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-16 | 0 | 無測試套件 | 疲勞警報事件偵測邏輯已完成 |
| `server/routers/` | 2026-04-16 | 0 | 無測試套件 | 8 個 router 全部有 docstring |
| `simulator/` | 2026-04-16 | 0 | 無測試套件 | engine time_scale setter 已補 docstring |
| `simulator/physics/` | 2026-04-16 | 0 | 無測試套件 | 新增齒輪嚙合邊帶分析模型 |
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
- SCADA 標籤：88 個（新增 4 個齒輪邊帶標籤，原 84 個）

## 今日新增功能

### 齒輪嚙合邊帶分析模型（#58）
- **物理原理**：齒輪嚙合在 GMF（齒數 × 軸頻）產生振動。齒輪缺陷（磨損、裂紋）造成振幅調變，在 GMF 兩側產生邊帶（GMF ± n×f_shaft）。邊帶振幅是齒輪箱健康的關鍵診斷指標。
- **實作方式**：
  1. `vibration_spectral.py`：新增 GMF 計算與邊帶模型
  2. GMF = rotor_RPM × gear_teeth / 60（ring gear 97 齒）
  3. 健康齒輪：邊帶約 GMF 振幅的 3%（一階）和 1.5%（二階），加隨機噪聲
  4. gearbox_overheat 故障：一階邊帶 +0.20 mm/s × severity，二階 +0.10 mm/s × severity
  5. 邊帶能量比（sideband_ratio）= 邊帶總能量 / GMF 振幅（>0.3 表示缺陷）
  6. 所有新欄位均帶低通平滑和非負限制
- **新增 SCADA 標籤**：
  - `WVIB_GmfFreq`：齒輪嚙合頻率（Hz）
  - `WVIB_Sideband1Amp`：一階邊帶振幅（mm/s）
  - `WVIB_Sideband2Amp`：二階邊帶振幅（mm/s）
  - `WVIB_SidebandRatio`：邊帶能量比
- **預期效果**：
  - 額定轉速 ~22 RPM 下，GMF ≈ 35.6 Hz
  - 正常運轉時 sideband_ratio < 0.10
  - 注入 gearbox_overheat 故障後，邊帶振幅明顯上升，ratio > 0.30
  - 可作為齒輪箱狀態監測的早期缺陷指標

## 建議行動

1. **合併邊帶分析模型**：已推送至 `claude/happy-goodall-Mov9d`，可建立 PR 合併
2. **完成 #58 頻帶警報閾值曲線**：各頻帶加入基於工況的動態警報閾值
3. **實作 #58 峰值因子/峭度異常警報**：crest factor 和 kurtosis 超標自動告警
4. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
5. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
6. **完善 #57 前端視覺化**：前端新增 RUL 顯示和疲勞警報等級視覺化
