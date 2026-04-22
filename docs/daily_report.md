# digiWindFarm Daily Report

> 最後更新：2026-04-22

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-ujMjS`）：
- feat: atmospheric stability couples diurnal cycle to shear α and TI (#99)

近 24 小時主幹 `main` 合併摘要：
- [d5b9adb] Merge PR #98 — 偏航引發尾流偏轉文件同步
- [f96ec88] docs: update project docs and daily report for yaw-induced wake deflection (#97)
- [8d520c8] feat: add yaw-induced wake deflection (Bastankhah 2016 wake steering) (#97)
- [ea9ffae] Merge PR #96 — 動態尾流蜿蜒文件同步
- [bf24c3a] docs: update project docs and daily report for dynamic wake meandering (#95)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立 | #99 | 大氣穩定度 Monin-Obukhov — 日週期風切指數 α 與亂流強度 TI 耦合 | 今日建立並實作 |
| 實作 | #99 | 大氣穩定度日週期耦合 | 新增 `WMET_ShearAlpha` + `WMET_AtmStab`，5 項自測全過 |
| 保持 | #97 | 偏航引發尾流偏轉 | 昨日已實作並合併 main |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日建立 1 個 issue（#99），符合「每次最多 3 個新 issue」規則。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #99 | 大氣穩定度 Monin-Obukhov 日週期耦合 | enhancement, physics, auto-detected | 2026-04-22 | 已實作 |
| #97 | 偏航引發尾流偏轉 — Bastankhah 2016 | enhancement, physics, auto-detected | 2026-04-21 | 已合併 main |
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
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-22 | 0 | 無測試套件 | `engine.py` 新增穩定度/α/TI_mult 計算與傳遞 |
| `simulator/physics/` | 2026-04-22 | 0 | 無測試套件 | `turbine_physics` 接收 `wind_shear_exp_base`/`atm_stability` kwargs、`scada_registry` 新增 `WMET_ShearAlpha`/`WMET_AtmStab` |
| `wind_model.py`（根目錄） | 2026-04-22 | 0 | 無測試套件 | 新增 `get_atmospheric_stability`/`get_shear_exponent`/`get_turbulence_multiplier` |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 58 個路由（57 HTTP + 1 WebSocket）。無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile simulator/physics/{turbine_physics,scada_registry}.py simulator/engine.py wind_model.py` — 4 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**99 個**（+2：`WMET_ShearAlpha`、`WMET_AtmStab`）

## 今日新增功能

### 大氣穩定度日週期耦合 Atmospheric Stability Coupling（#99）

**物理原理**

離岸/陸上邊界層有強烈的**日週期穩定度循環**，這是所有長期量測資料共同觀察到的現象：

| 時段 | 穩定度 | 典型 α | 典型 TI | 物理成因 |
|------|-------|-------|---------|----------|
| 深夜/清晨 | 強穩定 | 0.25–0.35 | 0.05–0.08 | 地表輻射冷卻 → 近地層溫度反轉 → 抑制垂直混合 |
| 日出/日落 | 中性 | 0.14 | 0.10 | 熱平衡過渡期 |
| 正午/午後 | 強不穩定 | 0.06–0.12 | 0.12–0.18 | 太陽加熱地表 → 熱浮力 → 激烈垂直混合 |
| 強風或陰天 | 機械/中性 | 趨近 0.14 | 趨近 0.10 | 機械混合或雲層削弱日射效應 |

使用連續穩定度分數 `s ∈ [−1, +1]`：
```
s = solar(t) × wind_damping(V) × cloud_damping(pressure)

solar(t)       = sin(π · (hour − 6)/12)               # +1 正午、0 晨昏、−1 午夜
wind_damping   = 1 / (1 + (V/8)²)                      # 強風機械混合壓低 |s|
cloud_damping  = 1 − 0.5 · max(0, −pressure_state)     # 低壓鋒面雲層削弱
```

對應風切與 TI：
```
α(s)      = clamp(0.14 − 0.10·s, 0.04, 0.30)
TI_mult(s)= clamp(1.0 + 0.5·s,   0.5,  1.6)
```

**實作方式**

1. `wind_model.py::WindEnvironmentModel`：
   - `get_atmospheric_stability(timestamp)` → 連續分數 [-1, +1]
     - 手動 override 時回 0.0（中性）
     - 無副作用：重構為使用 `_weather._pressure_state` 直接讀取，不再呼叫 `_get_auto_wind`，每步可多次呼叫而不改變 RNG 狀態
   - `get_shear_exponent(timestamp, stability=None)` → α
   - `get_turbulence_multiplier(timestamp, stability=None)` → TI 倍率
   - 新的 `stability` 可選參數允許呼叫端預先計算 s 後共享，避免重複計算

2. `simulator/engine.py`：
   - 每步計算 `atm_stability` 一次，然後傳入 `get_shear_exponent(stability=s)` 與 `get_turbulence_multiplier(stability=s)` 避免重複
   - `effective_ti = wind_model.turbulence_intensity × TI_mult`
   - 同時餵給 `_turbulence_gen.step(ti=effective_ti)` 與 `_per_turbine_wind.step(..., effective_ti, ...)`
   - 每台風機 `turbine.step(..., wind_shear_exp_base=shear_alpha, atm_stability=atm_stability)`

3. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `wind_shear_exp_base: float = 0.2` 與 `atm_stability: float = 0.0` kwargs
   - `_individuality` 的 `wind_shear_exp` 鍵**重新命名**為 `wind_shear_exp_offset`，語意從「絕對 α」改為「永久偏置」（±0.04~+0.06）
   - `_effective_shear_alpha = clamp(wind_shear_exp_base + offset, 0.04, 0.35)`，用於 1P 風切扭矩調變與疲勞計算
   - `__init__` 與 `reset()` 初始化新狀態 `_effective_shear_alpha`、`_atm_stability`
   - SCADA 輸出新增 `"WMET_ShearAlpha"` 與 `"WMET_AtmStab"`

4. `simulator/physics/scada_registry.py`：
   - 新增 `ScadaTag("WMET_ShearAlpha", ..., "REAL32", "-", ..., 0.0, 0.4)`
   - 新增 `ScadaTag("WMET_AtmStab", ..., "REAL32", "-", ..., -1.0, 1.0)`
   - **SCADA 總數從 97 增為 99**

**物理效應（自測驗證）**

`WindEnvironmentModel(seed=42)`，2026-04-22：

| 時段 | 預期 s | 實測 s | α | TI_mult | 結果 |
|------|--------|--------|---|---------|------|
| 02:00（夜） | s ≤ −0.35 | **−0.459** | 0.186 | 0.770 | ✓ |
| 06:00（晨） | s ≈ 0 | **+0.000** | 0.140 | 1.000 | ✓ |
| 13:00（午） | s ≥ 0.35 | **+0.512** | 0.089 | 1.256 | ✓ |
| 18:00（昏） | s ≈ 0 | **+0.000** | 0.140 | 1.000 | ✓ |
| 21:00（夜） | 負 | **−0.422** | 0.182 | 0.789 | ✓ |
| 手動 override 8 m/s@noon | s=0 強制中性 | **0.000** | 0.140 | 1.000 | ✓ |
| V=20 m/s 機械混合 | wind_damping ≤ 0.15 | **0.138** | — | — | ✓ |

Engine 端整合：
- 3 台風機在同一步同時收到共用的 `atm_stability`（已追溯至 turbine.step 的 kwargs，完全一致）
- per-turbine α 結構性差異保留（spread 0.07–0.12，由 `wind_shear_exp_offset` 驅動）
- SCADA 輸出 `WMET_AtmStab`/`WMET_ShearAlpha` 在前後兩步之間平滑變化（無瞬跳）

**影響範圍**

- **風切 α** 現在依時間變動，而不是固定 0.2：夜間 α 升到 0.18–0.22，白天降至 0.08–0.11。這會直接反映在 #71 的 1P 葉片扭矩調變和 #72 的葉片疲勞計算上
- **TI_mult** 直接乘上基準 `turbulence_intensity`：夜間亂流下降到 60–80%，白天放大到 120–140%。會影響：
  - #95 動態尾流蜿蜒（σ_θ=0.3·TI 之基線變動）
  - #93 Bastankhah 尾流擴展率（k*=0.38·TI+0.004）
  - 全場每步的湍流分量（`_turbulence_gen`）與每台風機的永久湍流（`_per_turbine_wind._turb_gens`）
- 新 SCADA 標籤 `WMET_ShearAlpha`、`WMET_AtmStab` 可於歷史圖表觀察 24 小時週期，或用於後續故障診斷的「日週期基線校正」
- 與 #89（濕度）、#91（局部亂流）、#93/#95/#97（尾流）共用 `WindEnvironmentModel` 的 `_weather._pressure_state` 軌跡，所以天氣鋒面會**同時**影響風切/TI、濕度、尾流 — 系統性自洽

**為何這是物理「因」而非輸出偏移**

- 根源於時間（日週期）與環境（風速、雲量）的真實物理驅動
- 經由 α、TI 兩個**已存在**的物理參數路徑傳遞到所有下游模型（風切葉片負載、尾流擴展、湍流產生器）
- 每台風機仍有**永久 α 偏置**（`wind_shear_exp_offset`）疊加在時變基線之上：持續差異 + 時間過渡雙重觀察
- 手動 override 自動切回中性，避免 demo 時穩定度「莫名其妙變動」

## 建議行動

1. **長時段資料品質驗證**：以 `examples/data_quality_analysis.py` 跑 24 h 自動模式（time_scale=60），觀察：
   - `WMET_AtmStab` 是否呈現日週期正弦波
   - `WMET_ShearAlpha` 夜間是否 0.18–0.22、白天是否 0.08–0.11
   - 塔架疲勞損傷率是否夜間升高（高剪切 → 1P 負載放大）
2. **前端視覺化**：Dashboard 可新增穩定度熱圖或時間軸，標註白天/夜間區段
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **建立 pytest 測試套件（#52）**：α(s)、TI_mult(s)、override 中性化為理想首批單元測試案例
6. **未來擴充**：
   - 海氣溫差（Sea-Air ΔT）驅動穩定度（目前用 `_pressure_state` 作代理）
   - Low-level Jet（LLJ）夜間風速剖面
   - 風切與葉片飛彈負載的非對稱性（轉子上下半部 V² 差異）
7. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
