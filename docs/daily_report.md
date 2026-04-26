# digiWindFarm Daily Report

> 最後更新：2026-04-25（分支 `claude/keen-hopper-aUvgm`）

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-aUvgm`）：

- feat: couple atmospheric stability to wake meander timescale τ_m (#113)
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #113

近 48 小時主幹 `main` 合併摘要：

- [7dc8c1b] Merge PR #112 — 大氣穩定度 × 風切偏向耦合 (#111)
- [5e9c2b2] feat: couple atmospheric stability to wind veer (Ekman) (#111)
- [6a48943] Merge PR #110 — 大氣穩定度 × Bastankhah 尾流擴張耦合 (#109)
- [8223232] feat: couple atmospheric stability to Bastankhah wake expansion k* (#109)
- [4af85e2] Merge PR #107 — 大氣壓動態耦合文件同步
- [4b78380] feat: couple ambient pressure to synoptic weather state (#106)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立+實作 | #113 | 大氣穩定度 × 動態尾流蜿蜒 τ_m 耦合 | `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組現為 **0 錯誤** |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日建立 1 個 issue（#113）並完成實作；尚未關閉（待 PR 合併後關閉）。符合「每次最多 3 個新 issue / 1 個 PR」規則。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #113 | 大氣穩定度 × 動態尾流蜿蜒 τ_m 耦合 | enhancement, physics, auto-detected | 2026-04-25 | 已實作於本分支 |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 115 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤 |
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `simulator/physics/wind_field.py` | 2026-04-25 | 0 | 無測試套件 | `_update_wake_meander` 加 `stability` 參數，τ 由 25 s 改為 `25·clamp(1−0.6·s, 0.4, 2.0)` s |
| `simulator/physics/turbine_physics.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（沿用 #111） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `simulator/engine.py` | 2026-04-24 | 0 | 無測試套件 | 無變更（`atm_stability` 已於 #109 傳入 `PerTurbineWind.step`，本次只是新增向 `_update_wake_meander` 的內部轉發） |
| `simulator/physics/scada_registry.py` | 2026-04-24 | 0 | 無測試套件 | 無變更（102 個物理標籤保持） |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 61 個 HTTP 路由 + 1 WebSocket。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節（追蹤項，不阻塞物理模型優先工作）。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/physics/wind_field.py` — 通過
- 引擎端到端 smoke test（`WindFarmSimulator(turbine_count=3)` 走 20 步 `_run_one_step(datetime.now(), 1.0)`）— 通過，3 台輸出 SCADA `WMET_WakeMndr` / `WMET_AtmStab` 正常
- 物理單元自測（`/tmp/test_stability_meander.py`）— **6 / 6 PASS**
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**102 個**（#113 無新增標籤，觀察性透過既有 `WMET_WakeMndr × WMET_AtmStab` 自相關達成）

## 今日新增功能

### 大氣穩定度 × 動態尾流蜿蜒 τ_m 耦合 — #113

**問題與物理原理**

#95 已實作 Larsen-DWM 動態尾流蜿蜒，採用 AR(1) 過程：

```
σ_θ ≈ 0.3 · TI       (Larsen 2008)
τ_m = 25 s（固定）   (atmospheric integral timescale)
```

但 `τ_m = L_u / U` 的 **積分時間尺度** 強依賴大氣穩定度：

| 大氣狀態 | L_u (m, hub-height streamwise) | τ_m @ 8 m/s | 物理機制 |
|---------|------------------|-------------|---------|
| 穩定（夜間 / s≈−1） | 250–500 | 30–60 s | 抑制垂直混合，渦旋 footprint 拉長 |
| 中性（s≈0） | 150–200 | 20–25 s | baseline |
| 對流（午後 / s≈+1） | 80–150 | 10–18 s | 強烈渦旋翻攪、L_u 縮短 |

來源：Counihan (1975) *Atmos. Environ.* 9, 871–905；Larsen et al. (2008) *Wind Energy* 11, 289–301；Peña & Hahmann (2012) *Wind Energy* 15, 717–731；IEC 61400-1 ed.4 Annex C。

**公式與實作**

```
τ_m_eff = 25.0 · clamp(1.0 − 0.6 · s,  0.4, 2.0)   [s]
```

對應映射：

| s | factor | τ_m | 物理解讀 |
|---|--------|-----|---------|
| −1.0（穩定） | 1.6 | 40 s | 慢蜿蜒、渦旋停留時間長 |
| −0.5 | 1.3 | 32.5 s | 略慢於中性 |
| 0.0（中性） | 1.0 | 25 s | baseline（與 #95 一致） |
| +0.5 | 0.7 | 17.5 s | 略快 |
| +1.0（對流） | 0.4 | 10 s | 快速翻攪 |

clamp `[0.4, 2.0]` 防止極端 s 落入非物理區。`σ_θ` 維持只跟 TI 走（既有 #99 已透過 TI mult 把對流時段拉高 1.5×，因此 **振幅與時間尺度兩條路同時改變但職責分離**）。

**實作檔案**

`simulator/physics/wind_field.py`（單檔，淨增 +6 / −2 行）：
- `step()` 將既有 `atm_stability` 透過 `stability=` kwarg 傳入 `_update_wake_meander`
- `_update_wake_meander(turbulence_intensity, dt, stability=0.0)`：在原 `tau = 25.0` 上方計算 `tau_factor = clamp(1 − 0.6·s, 0.4, 2.0)`，`tau = 25.0 * tau_factor`

`simulator/engine.py`：無需變更（`atm_stability` 已於 #109 傳入 `PerTurbineWind.step(...)`）

**自測驗證（`/tmp/test_stability_meander.py` 4000 s AR(1)，TI=0.10）**

| s | 預期 τ | 實測 σ | 實測 AC(25s) | 理論 exp(−25/τ) | AC(50s) | ZCR |
|---|-------|-------|-------------|-----------------|---------|------|
| −1.00（穩定） | 40 s | 5.60 m | **+0.452** | 0.535 | +0.208 | 0.0823 |
| 0.00（中性） | 25 s | 5.74 m | +0.283 | 0.368 | +0.080 | 0.0975 |
| +1.00（對流） | 10 s | 5.97 m | **+0.010** | 0.082 | −0.031 | 0.1395 |

| 驗證項 | 預期 | 實測 | 結果 |
|--------|------|------|------|
| τ 映射 s→{40, 25, 10} | 精確 | 40.00 / 25.00 / 10.00 s | ✓ |
| AC(25 s) stable > convective | Δ ≥ 0.30 | Δ = 0.442 | ✓ |
| 中性 AC(25 s) | [0.25, 0.50] | 0.283 | ✓ |
| 穩定 AC(25 s) | [0.40, 0.65] | 0.452 | ✓ |
| 對流 AC(25 s) | [0.0, 0.20] | 0.010 | ✓ |
| 穩定 ZCR < 對流 ZCR · 0.6 | < 0.084 | 0.082 | ✓ |
| σ 跨穩定度差異 | < 30 % | 6.2 % | ✓ |

**為何這是物理「因」而非輸出偏移**

- τ 是 AR(1) 過程的本質參數，直接改變 `α = exp(−dt/τ)` 與雜訊縮放係數 `√(1−α²)`
- 蜿蜒角度 `θ_m[j]` 為 `_update_wake_factors` 內既有 Bastankhah 迴圈的位移輸入；θ_m 的時間特性改變 → 下游 `r_lat` 改變 → `exp(−0.5·r_lat²/σ²)` 改變 → 下游 `WMET_WakeDef` 與葉片載荷自然反映
- 不在 `WMET_WakeMndr` 加修正項；不引入新標籤
- 全場共享同一穩定度（物理事實，符合 ABL 一致性）
- 與 #99（α / TI）、#101 / #106（ρ）、#109（k\*）、#111（veer）形成完整 ABL 物理鏈

**觀察性**

- 不新增 SCADA 標籤
- 夜間穩定時段：`WMET_WakeMndr` 自相關時間延長，下游 `WMET_WakeDef` 變動更平滑、低頻能量增加
- 對流午後：`WMET_WakeMndr` 高頻擺動增強，下游 `WMET_WakeDef` 變動更隨機
- 與 #99（TI mult 0.5–1.6×）疊加 → 完整刻畫「夜間慢且小、午後快且大」的真實尾流節奏
- 與 #109（夜間 wake 變深 +34 %）+ #111（夜間 TwrSS +37 %）疊加 → 下游風機在穩定夜間 fatigue DEL 預期再增 3–8 %（慢蜿蜒讓側向偏載更持久）

## 建議行動

1. **長時段資料品質驗證**：跑 `examples/data_quality_analysis.py` **24 小時自動模式**，觀察：
   - `WMET_WakeMndr × WMET_AtmStab` 的 lag-25 s 自相關差異（穩定夜間應 ≥ 0.4，對流午後應 ≤ 0.15）
   - 下游風機 `WMET_WakeDef` 標準差的日週期：穩定夜間應降低（慢蜿蜒）、對流午後應升高（快速翻攪 + 振幅大）
   - 與 #109 / #111 疊加：穩定夜間下游機塔架 DEL 上升幅度
2. **建立 pytest 測試套件（#52）**：本日 `/tmp/test_stability_meander.py` 加上既有 `/tmp/test_stability_veer.py`（#111）、`/tmp/test_stability_wake.py`（#109）已有三個成熟單元自測腳本，建議共同移入 `tests/physics/` 作為 pytest 起點
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **未來擴充**：
   - σ_θ 的風速依賴（目前純 TI 耦合；文獻有指出 σ_v ≠ TI · U 在強剪切下需修正）
   - 半日大氣潮 S2 解耦（中緯度 ±0.3 hPa）
   - curled-wake 模型（偏航尾流的 counter-rotating vortex pair）
   - σ_y 的距離依賴 `σ_y(x) = 0.3 · σ_v · x / U`（目前用單一 θ·x 線性近似）
6. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
7. **F401 清理**：`turbine_model.py`、`dashboard.py`、`scada_system.py` 等根目錄早期原型檔案的 unused import 仍存在（追蹤 #44）

## 通知

已透過 email 發送日報至 moredof@gmail.com（請依專案實際 email 通知管道配置執行）。
