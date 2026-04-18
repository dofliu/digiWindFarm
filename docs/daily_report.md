# digiWindFarm Daily Report

> 最後更新：2026-04-18

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/dazzling-carson-Hzaba`）：
- feat: add gear tooth contact model — mesh stiffness ripple + tooth wear (#76)

過去 24 小時主要合併/提交：
- [811f689] Merge PR #87 — 風向隨高度偏轉模型（#79，Ekman 螺旋）
- [bf933de] docs: update daily report and project docs for 2026-04-17 fourth run
- [1266ec3] feat: add wind veer model with Ekman spiral blade direction offset (#79)
- 另有分支 `claude/dazzling-carson-Es3vc` 實作 Bastankhah-Porté-Agel 高斯尾流模型（#86，尚未合併至 main）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #76 | 齒輪齒面接觸模型 | 已實作：接觸比 ε_α 嚙合剛度漣波 + 齒面磨耗指數 + GMF HSS 扭振耦合 |
| 保持 | #86 | 進階尾流模型（Bastankhah） | 已於 `claude/dazzling-carson-Es3vc` 分支實作，等待合併 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日未建立新 issue（目前的 open issues 已涵蓋待辦項目，符合「每次最多 3 個新 issue」規則）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 115 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-18 | 0 | 無測試套件 | drivetrain_model、vibration_spectral、turbine_physics、scada_registry 新增齒面接觸（#76） |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 58 個路由（57 HTTP + 1 WebSocket）。無新增路由，狀態與昨日相同。詳見 README.md「Core APIs」章節。

新增/待同步：`/api/farms`（4 個路由）仍未同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 server/ + simulator/ 維持 0 錯誤，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- `ruff check simulator/physics/{drivetrain_model,vibration_spectral,turbine_physics,scada_registry}.py` — All checks passed ✓
- `python -m py_compile` — 4 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**92 個**（+1：`WDRV_GbxToothWear`）

## 今日新增功能

### 齒輪齒面接觸模型（#76）

**物理原理**
- 真實齒輪嚙合時，接觸齒數於單齒區／雙齒區交替，嚙合剛度 K 呈週期性變化。
- 接觸比 ε_α（typical 1.3–1.8）越小，單齒區佔比越大 → 嚙合漣波越強。
- 齒面磨耗（Archard）隨滑動速度 × 接觸應力累積，粗糙度上升使漣波幅值放大，並在 GMF 邊帶產生調變。

**實作方式**
1. `drivetrain_model.py`：
   - `DrivetrainSpec` 新增 `hss_pinion_teeth=23`、`contact_ratio=1.55`、`mesh_stiffness_ripple_base=0.04`、`tooth_wear_rate_per_hour=3.5e-6`。
   - State 新增 `_mesh_phase`、`_tooth_wear_index`。
   - `step()` 計算每步相位 `phase += 2π × GMF × dt`，產生 cos 漣波並乘以 HSS 平均扭矩 → `gmf_excitation_knm`。
   - 漣波項以 `0.015 × gmf_exc_knm` 加入 HSS 扭振方程。
   - 磨耗累積：`dwear/dt = rate × speed_norm × load_norm × (1 + 6·overheat_sev)`。
   - 暴露 `tooth_wear_index`、`mesh_stiffness_variation`、`gmf_excitation_knm` 屬性。
   - `reset()` 保留磨耗（資產持續狀態），新增 `reset_wear()` 供大修後歸零。
2. `vibration_spectral.py`：
   - `step()` 新增 `tooth_wear_index`、`mesh_stiffness_ripple` 參數。
   - `band_gear_x/y` 加入 `contact_ripple + wear_gear` 項；sideband_1/2 的係數隨 `tooth_wear_index` 線性上升。
3. `turbine_physics.py`：
   - 傳遞 `gearbox_overheat_severity` 至 drivetrain.step（從 active_faults 擷取）。
   - 傳遞 `tooth_wear_index`、`mesh_stiffness_ripple` 至 vib_spectral.step。
   - 新增 SCADA 輸出 `WDRV_GbxToothWear = wear × 100%`。
4. `scada_registry.py`：
   - 新增 `WDRV_GbxToothWear`（REAL32, %, 0–150, 中文「齒面磨耗指數」）。

**物理效應（自測）**
- 健康狀態：`mesh_stiffness_variation = 0.018`，`gmf_excitation_knm ≈ ±0.19 kNm`（rated 工況）。
- 正常磨耗：800 MWh 約累積 wear ≈ 1.8e-7 → 幾千小時後達到可觀察等級（符合真實風場維護尺度）。
- `gearbox_overheat` 嚴重度 0.8：磨耗累積速率 × 5.8 倍。
- Direct-drive 風機：ripple = 0（正確略過）。

**影響範圍**
- GMF 振動（`WVIB_BandGear*`）於滿載時隨 wear 線性上升。
- `WVIB_Sideband1/2Amp` 在 wear=0.6 時係數由 0.03 升至 0.27（9× 增幅），`sideband_ratio` 成為磨耗早期指標。
- HSS 扭振（`torsion_vib_hss`）獲得 GMF 週期激振成分，使齒輪箱振動 trend 更真實。
- 為後續 #58 頻譜警報曲線提供物理因果（warning → mesh stiffness ripple；alarm → wear 60%+）。

## 建議行動

1. **合併 `claude/dazzling-carson-Es3vc`（#86 尾流模型）至 main**：該分支已完成 Bastankhah-Porté-Agel 實作但尚未建立 PR。
2. **同步 `/api/farms` 4 個路由至 README.md**：昨日建議仍未完成。
3. **實作 #58 頻譜警報曲線**：目前齒面接觸已提供物理因果，可將 `tooth_wear_index` 對應至 frontend 警報等級。
4. **建立測試套件（#52）**：本日新增的 mesh stiffness 與 wear 累積具有明確數值預期，適合做為物理模型 pytest 的首個案例。
5. **實作 #57 前端 RUL 視覺化**：後端已就緒，前端 Load/Fatigue 分頁補 RUL 顯示。
