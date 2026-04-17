# digiWindFarm Daily Report

> 最後更新：2026-04-17（第二次）

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/gifted-noether-XnOBT`）：
- [a7f000b] feat: add blade mass imbalance with centrifugal force ω² coupling (#72)

過去 24 小時合併至 main：
- [887b38b] Merge pull request #74（風切剖面模型 — 文件更新）
- [4982827] Merge pull request #70（塔架陰影效應 — 3P 功率/扭矩/載荷調變）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作完成 | #72 | 葉片質量不平衡與轉子動態不平衡模型 | 已實作：離心力 F=Δm×r_cg×ω² + 1P 振動耦合 + 載荷耦合，待合併 |
| 已關閉 | #73 | 齒輪箱油溫與黏度效應模型 | 前次工作已完成並關閉 |
| 新建 | #75 | 冷卻液液位與洩漏偵測模型 | physics_model_status.md 缺口 |
| 新建 | #76 | 齒輪齒面接觸模型 — 嚙合剛度與載荷分布 | physics_model_status.md 缺口 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電氣模型尚未加入保護曲線比對邏輯 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | BPFO/BPFI + 邊帶 + 峰值因子/峭度已完成，頻帶警報曲線待做 |
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
| #76 | 齒輪齒面接觸模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #75 | 冷卻液液位與洩漏偵測模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #72 | 葉片質量不平衡模型 | enhancement, physics, auto-detected | 2026-04-17 | 已實作，待合併 |
| #71 | 風切剖面模型 | enhancement, physics, auto-detected | 2026-04-17 | 已合併 |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | LVRT/OVRT 保護曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
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
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `server/routers/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-17 | 0 | 無測試套件 | 新增葉片質量不平衡 (#72) |
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
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：94 個（+1 新增 WROT_ImbForce）

## 今日新增功能

### 葉片質量不平衡模型（#72）
- **物理原理**：三支葉片因製造公差存在質量差異（典型 ±0.5%），轉動時產生離心不平衡力 F = Δm × r_cg × ω²，隨轉速平方增長。此力以轉子 1P 頻率旋轉，是 1P 振動的物理根源。
- **實作方式**：
  1. `turbine_physics.py`：每台風機在初始化時產生 3 支葉片的質量偏移（常態分佈 σ=0.5%），計算每個時步的合成離心不平衡力向量
  2. `vibration_spectral.py`：1P 頻帶從線性 speed_ratio 改為 speed_ratio² 耦合，加入不平衡力直接貢獻（Y 方向 1.1× 係數，反映側向主導）
  3. `fatigue_model.py`：不平衡力耦合至塔架側向彎矩（取代原隨機噪聲），加入葉片揮舞彎矩貢獻
  4. `scada_registry.py`：新增 `WROT_ImbForce` 標籤（轉子不平衡力，kN）
- **物理效果**：
  - 每台風機有獨特的 1P 振動指紋
  - 1P 振動 ∝ ω²（非線性，符合離心力物理）
  - 低速時幾乎無不平衡振動，額定轉速時最大
  - 力傳遞路徑：轉子 → 主軸承 → 塔架側向彎矩
  - 故障疊加：blade_icing 和 pitch_imbalance 的 1P 效應保持不變

## 建議行動

1. **合併葉片質量不平衡模型**：已推送至 `claude/gifted-noether-XnOBT`，可建立 PR 合併
2. **實作 #75 冷卻液液位與洩漏偵測**：漸進式故障指標，適合預測性維護分析
3. **實作 #76 齒輪齒面接觸模型**：時變嚙合剛度 + 齒面磨耗進程，提升 GMF 振動真實度
4. **實作 #67 保護繼電器協調**：LVRT/OVRT 電壓-時間保護曲線與保護動作序列
5. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
6. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
