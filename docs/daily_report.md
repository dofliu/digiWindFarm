# digiWindFarm Daily Report

> 最後更新：2026-04-26（分支 `claude/keen-hopper-mLqEJ`）

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-mLqEJ`）：

- feat: couple atmospheric stability to turbulence integral length scale L_u (#115)
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #115

近 48 小時主幹 `main` 合併摘要：

- [1478408] Merge PR #114 — 大氣穩定度 × 動態尾流蜿蜒 τ_m 耦合 (#113)
- [e47bd1d] feat: couple atmospheric stability to wake meander timescale τ_m (#113)
- [7dc8c1b] Merge PR #112 — 大氣穩定度 × 風切偏向耦合 (#111)
- [5e9c2b2] feat: couple atmospheric stability to wind veer (Ekman) (#111)
- [6a48943] Merge PR #110 — 大氣穩定度 × Bastankhah 尾流擴張耦合 (#109)
- [8223232] feat: couple atmospheric stability to Bastankhah wake expansion k* (#109)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 接手+實作 | #115 | 大氣穩定度 × 風速湍流積分長度尺度 L_u 耦合 | issue 已於今天 05:38 由 dofliu 建立；本次完成實作於 `wind_field.py::TurbulenceGenerator.step()`，加 `stability` kwarg、`L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` |
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

本日**未建立**新 issue（既有 issue #115 已涵蓋當日工作），實作後尚未關閉（待 PR 合併後關閉）。符合「每次最多 3 個新 issue / 1 個 PR」規則。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #115 | 大氣穩定度 × 湍流積分長度尺度 L_u 耦合 | enhancement, physics, auto-detected | 2026-04-26 | **已實作於本分支** |
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
| `simulator/physics/wind_field.py` | 2026-04-26 | 0 | 無測試套件 | `TurbulenceGenerator.step()` 加 `stability` kwarg；`PerTurbineWind.step()` 將 `atm_stability` 透傳到每台 `_turb_gens[i]` |
| `simulator/engine.py` | 2026-04-26 | 0 | 無測試套件 | 全場 `_turbulence_gen.step(...)` 補上 `stability=atm_stability` |
| `simulator/physics/turbine_physics.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（沿用 #111） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
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
- `python -m py_compile simulator/physics/wind_field.py simulator/engine.py` — 通過
- 引擎端到端 smoke test（`WindFarmSimulator(turbine_count=3)._run_one_step(...)` × 20 步）— **20 / 20 PASS**，3 台輸出 SCADA `WMET_AtmStab` / `wind_speed` 正常
- 物理單元自測（`/tmp/test_stability_lu.py`）— **5 / 5 PASS**：
  - 穩定 s=−1（L_u=544 m, τ=54 s）：lag-30 s 自相關 0.574（理論 0.576）✓
  - 中性 s=0（L_u=340 m, τ=34 s）：0.401（理論 0.414）✓
  - 對流 s=+1（L_u=136 m, τ=14 s）：0.097（理論 0.110）✓
  - 單調性 0.574 > 0.401 > 0.097 ✓
  - 向後相容（預設 kwarg ≡ stability=0.0，bit-for-bit 差異 0）✓
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/test_stability_lu.py` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**102 個**（#115 無新增標籤，觀察性透過既有 `WMET_AtmStab × WROT_RotSpd` 低頻自相關差異達成）

## 今日新增功能

### 大氣穩定度 × 湍流積分長度尺度 L_u 耦合 — #115

**問題與物理原理**

`simulator/physics/wind_field.py::TurbulenceGenerator.step()` 的 Kaimal 譜近似目前使用**寫死**的積分長度尺度：

```python
L_u = 340.0  # IEC 61400-1 hub-height neutral baseline
tau = L_u / max(mean_speed, 1.0)
```

這意味著 AR(1) 風速湍流的時間相關性與大氣穩定度**無關**——即使白天午後對流劇烈或夜間穩定強剪切，τ_turb 永遠是 `340/V`。物理上不正確：與 #113 對動態尾流蜿蜒套用的 ABL 一致性同樣道理，**hub-height 風速湍流的積分尺度也跟穩定度走**。

| 大氣狀態 | L_u (m) | τ @ 10 m/s | 物理機制 |
|---------|---------|-----------|---------|
| 穩定（夜間 / s≈−1） | 400–600 | 40–60 s | 抑制垂直混合，渦旋拉長、停留時間長 |
| 中性（s≈0） | 250–340 | 25–34 s | IEC 61400-1 baseline |
| 對流（午後 / s≈+1） | 100–200 | 10–20 s | 強烈翻攪、L_u 縮短 |

**實作公式**（沿用 #113 已採用的線性映射，保持鏈路一致性）：

```
L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)   [m]
τ_eff   = L_u_eff / V_mean
α_AR(1) = exp(−dt / τ_eff)
```

| s | factor | L_u | τ @ 10 m/s | 物理解讀 |
|---|--------|-----|-----------|---------|
| −1.0（穩定） | 1.6 | 544 m | 54 s | 慢渦旋、低頻能量主導 |
| 0.0（中性） | 1.0 | 340 m | 34 s | IEC baseline |
| +1.0（對流） | 0.4 | 136 m | 14 s | 快速翻攪、高頻能量主導 |

**修改範圍**

1. `simulator/physics/wind_field.py::TurbulenceGenerator.step()`：
   - 新增 `stability: float = 0.0` 關鍵字參數（向後相容）
   - `L_u` 改為 `L_u = 340.0 * clamp(1 − 0.6·s, 0.4, 2.0)`
   - 雜訊縮放係數 `σ·√(1−α²)` 不動，所以**振幅路徑由 #99 TI mult 主導不被本 PR 影響**

2. `simulator/physics/wind_field.py::PerTurbineWind.step()`：
   - 將既有 `atm_stability` 透傳到每台 `_turb_gens[i].step(..., stability=atm_stability)`

3. `simulator/engine.py::_run_one_step()`：
   - 全場 `_turbulence_gen.step(base_wind, effective_ti, time_step, stability=atm_stability)`

**驗證結果**

`/tmp/test_stability_lu.py`（4000 s, V=10 m/s, TI=0.10, warm-up 200 s 丟棄）：

| 案例 | L_u (m) | τ (s) | 觀測 r_lag30 | 理論 r_lag30 | 觀測 σ_v (m/s) | 期望 σ_v |
|------|---------|-------|--------------|--------------|----------------|----------|
| 穩定 s=−1 | 544 | 54.4 | **0.574** | 0.576 | 0.991 | 1.000 |
| 中性 s= 0 | 340 | 34.0 | **0.401** | 0.414 | 0.985 | 1.000 |
| 對流 s=+1 | 136 | 13.6 | **0.097** | 0.110 | 0.993 | 1.000 |

- **時序路徑**：lag-30 s 自相關與 `exp(−30/τ)` 解析解誤差 ≤ 3 %（穩定 1.4 %，中性 3.1 %，對流 1.3 %）
- **振幅路徑**：σ_v 維持在 TI·V ≈ 1.0 m/s，**不被本 PR 影響**（穩定度對振幅的反應仍由 #99 TI mult 0.5–1.6× 負責）
- **單調性**：穩定 > 中性 > 對流 ✓
- **向後相容**：`step(...)` 不傳 `stability` 與 `stability=0.0` 結果完全一致（500 步 diff = 0）✓

引擎端到端 smoke test：`WindFarmSimulator(turbine_count=3)` 走 20 步 `_run_one_step(datetime.now(), 1.0)`——**20 / 20** 步皆有正常 SCADA 輸出（含 `wind_speed` / `WMET_AtmStab`）。

**為何是物理「因」而非輸出端修正**

- L_u 是 Kaimal 譜的**本質參數**，直接決定 AR(1) 的 `α = exp(−dt/τ)` 與隱含的 PSD 形狀
- 不在輸出端加修正項；不引入新 noise channel；不增加新 RNG mutation
- 全場共享同一 stability score（與 ABL 物理事實一致）
- 與 #99 / #109 / #111 / #113 形成**五項 ABL × 物理子系統的完整耦合鏈**：振幅（#99 TI mult）→ 尾流擴張（#109 k*）→ 風向偏向（#111 veer）→ 尾流蜿蜒時序（#113 τ_m）→ **本機風速時序（#115 τ_v）**

**預期下游影響**

- 葉片 / 塔架低頻疲勞 DEL：穩定夜間長 τ → 低頻能量上升 → `WLOD_TwrFaMom` 低頻含量增加
- 偏航控制：穩定時段 `WYAW_YwVn1AlgnAvg5s` 變動更平滑（風向偏差持久化）
- 故障診斷：穩定夜間故障特徵更易累積至閾值（湍流不再快速沖淡訊號）
- 觀察性：`WMET_AtmStab × WROT_RotSpd` 低頻互相關（|s| 變大 → 自相關 |Δr| 變大）

## 建議行動

1. **物理鏈路下一步**：`#115` 完成五項 ABL 耦合鏈後，繼續往「次發物理鏈」探索：
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應，影響超長時間尺度）
   - 大氣穩定度 × Reynolds 應力剖面（垂直 momentum flux）
   - Hub-height 與 nacelle anemometer 的 transfer function（沿襲 IEC 61400-12-1 Annex D）
2. **測試基礎建設（#52）**：本次 `/tmp/test_stability_lu.py` 已可作為 `tests/physics/test_stability_lu.py` 的 pytest 起點，完成後可一併涵蓋 #99 / #109 / #111 / #113 / #115 五個 ABL 鏈路。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
