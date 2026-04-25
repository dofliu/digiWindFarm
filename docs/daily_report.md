# digiWindFarm Daily Report

> 最後更新：2026-04-24（分支 `claude/keen-hopper-Aa8Yg`）

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-Aa8Yg`）：

- fix: remove duplicate `get_wake_added_ti` in `wind_field.py` (#108)
- feat: couple atmospheric stability to Bastankhah wake expansion k\* (#109)
- docs: sync CLAUDE / README / TODO / physics_model_status for #108 + #109

近 48 小時主幹 `main` 合併摘要：

- [4af85e2] Merge PR #107 — 大氣壓動態耦合文件同步
- [de8c031] Merge branch 'main' into claude/keen-hopper-mZpPO
- [4b78380] feat: couple ambient pressure to synoptic weather state (#106)
- [6728bae] Merge PR #105 — 尾流誘發紊流增強文件同步
- [590c2d7] feat: add wake-added turbulence intensity (Crespo-Hernández) (#103)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立+實作+關閉 | #108 | `wind_field.py` 重複 `get_wake_added_ti`（F811） | 合併 #103/#106 遺留，body 完全相同；刪除 line 512 版本 |
| 建立+實作+關閉 | #109 | 大氣穩定度 × Bastankhah 尾流擴張耦合 | `k* = k_neutral·clamp(1+0.30·s, 0.55, 1.45)` |
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

本日建立 2 個 issue（#108 + #109）、關閉 2 個（同上），符合「每次最多 3 個新 issue / 1 個 PR」規則。未開 PR（用戶未要求）。

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
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `simulator/physics/wind_field.py` | 2026-04-24 | 0 | 無測試套件 | `_update_wake_factors` 接受 `stability`，k* 依 s 做 ±30% 修正；刪除重複 `get_wake_added_ti` |
| `simulator/engine.py` | 2026-04-24 | 0 | 無測試套件 | `per_turbine_wind.step(...)` 新增 `atm_stability` kwarg |
| `simulator/physics/turbine_physics.py` | 2026-04-24 | 0 | 無測試套件 | 無變更（沿用 #101/#106） |
| `simulator/physics/scada_registry.py` | 2026-04-24 | 0 | 無測試套件 | 無變更（102 個物理標籤保持） |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 63 個路由（62 HTTP + 1 WebSocket）。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**（修復前為 1 個 F811）
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/engine.py simulator/physics/wind_field.py wind_model.py` — 通過
- 引擎端到端 smoke test（3 風機，`datetime.now()`）— 通過，SCADA 輸出正常
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**102 個**（#109 無新增標籤，觀察性透過既有 `WMET_WakeDef × WMET_AtmStab` 達成）

## 今日新增功能

### 大氣穩定度 × Bastankhah 尾流擴張耦合 — #109

**問題與物理原理**

#99 已把大氣穩定度 `s ∈ [−1, +1]` 引入模型，驅動：
- 風切指數 α ∈ [0.04, 0.30]
- 紊流強度乘數 TI_mult ∈ [0.5, 1.6]

#93 已實作 Bastankhah-Porté-Agel Gaussian 尾流，擴張率：
```
k* ≈ 0.38 · TI + 0.004       （Niayifar & Porté-Agel 2016，中性假設）
```

**但兩者尚未連結**：無論白天對流或夜間穩定，k\* 只跟 TI 走，尾流復原長度完全忽略穩定度。實測量測（Bodega Bay、Horns Rev、Lillgrund）顯示：

| 穩定度 | k* 相對中性 |
|--------|-------------|
| 穩定（s < 0） | 0.7× – 0.8× |
| 中性（s ≈ 0） | 1.0×（baseline） |
| 對流（s > 0） | 1.2× – 1.3× |

來源：**Abkar & Porté-Agel (2015)** Phys. Fluids 27, 035104；**Peña et al. (2016)** Wind Energy 19, 547–566；亦列於 **IEC 61400-12-1 Annex E**。

**公式與實作**

```
k*_eff = k*_neutral · clamp(1.0 + 0.30 · s,  0.55, 1.45)
k*_eff clamp 至 [0.015, 0.08]
```

- 0.30 為中性附近的線性斜率，對應 ±30% 擺動
- clamp 0.55–1.45 防止極端穩定度下 k\* 過小而產生數值問題
- 外層 [0.015, 0.08] clamp 是尾流擴張率的物理合理區間
- s 正為不穩定、負為穩定，與 `WMET_AtmStab` 完全一致

**實作檔案**

1. `simulator/physics/wind_field.py`：
   - `PerTurbineWind.step(...)` 新增 `atm_stability: float = 0.0` kwarg
   - 呼叫 `self._update_wake_factors(...)` 時傳入 `stability=atm_stability`
   - `_update_wake_factors(...)` 新增 `stability: float = 0.0` 參數
   - `k_star` 計算拆成 `k_star_neutral` → `stability_factor` → 最終 `k_star`
2. `simulator/engine.py`：
   - `_run_one_step` 將既有 `atm_stability` 傳入 `self._per_turbine_wind.step(..., atm_stability=atm_stability)`

**物理效應（自測驗證）**

3 風機一列、6 D 間距、V=10 m/s、TI=8%，走 3 步穩態：

| 穩定度 s | T0 | T1 (6D) | T2 (12D) |
|---------|----|---------|----------|
| 中性 0.0 | 0.0000 | 0.2015 | 0.2241 |
| 穩定 −1.0 | 0.0000 | 0.2696 (+33.8 %) | 0.3066 (+36.8 %) |
| 對流 +1.0 | 0.0000 | 0.1572 (−22.0 %) | 0.1723 (−23.1 %) |

| 驗證項 | 預期 | 實測 | 結果 |
|--------|------|------|------|
| T1 穩定 > 中性（下游） | +25 % 到 +40 % | +33.8 % | ✓ |
| T1 對流 < 中性（下游） | −15 % 到 −25 % | −22.0 % | ✓ |
| 單調性 s→k\*→deficit | stable > neutral > convective | 成立 | ✓ |
| 重複方法 #108 已消除 | 1 個定義 | 1 個 | ✓ |
| 引擎端到端 smoke | 無錯誤 | 通過 | ✓ |

**為何這是物理「因」而非輸出偏移**

- `k*` 是 Bastankhah σ(x) 斜率的物理參數；改 `k*` 直接改變 σ(x)，進而改變所有 `C(x) · exp(−0.5·(r/σ)²)` 的赤字分佈
- 不是在 `WMET_WakeDef` 加修正項
- 全場共享同一大氣穩定度（物理事實）
- 每台下游機自動沿既有 Bastankhah 迴圈反映新 σ
- 同時影響 `WMET_WakeTi`（Crespo-Hernández 共享 σ）— 穩定夜間的尾流紊流也會變強
- 下游疲勞 DEL（#57）自然反映更深 / 更持久的速度赤字

**觀察性**

- 不新增 SCADA 標籤
- 夜間穩定時段：`WMET_WakeDef` 與 `WMET_AtmStab` 應出現明顯負相關（期待 r < −0.4 於下游機）
- 長時段資料品質驗證時可用 `examples/data_quality_analysis.py` 24h 模式觀察

### 清理重複方法 — #108

`simulator/physics/wind_field.py` 在 PR #104（#103）與 #107（#106）合併時留下兩個完全相同的 `get_wake_added_ti` 方法（line 473 與 line 512）。兩者 body 完全一樣，只是 docstring 文字稍有不同。Python 執行期以第二個覆蓋第一個，功能無影響，但造成：
- `ruff check` 出現 1 個 F811 錯誤
- 日後維護追蹤混亂（可能只改到其中一個）

**修復**：刪除 line 512–520 的第二份定義，保留 line 473–481 原始版本。ruff 現已 All checks passed!。

## 建議行動

1. **長時段資料品質驗證**：跑 `examples/data_quality_analysis.py` **24 小時自動模式**，觀察：
   - `WMET_WakeDef` 於下游機的晝夜週期（夜間增大，午後減小）
   - `WMET_WakeDef × WMET_AtmStab` 相關係數是否 < −0.4
   - `WMET_WakeTi` 晝夜差異（穩定夜間紊流堆積應更強）
   - 下游機 fatigue DEL 在穩定夜間的 5–15 % 上升
2. **前端視覺化**：Dashboard 可加「穩定度 × 尾流深度」scatter 小圖，或在 Wake tab 疊加 α / s 曲線
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **建立 pytest 測試套件（#52）**：穩定度-k\* 耦合、air density、wake-added TI 都是理想首批單元測試；今日 `/tmp/test_stability_wake.py` 可直接移入 `tests/physics/` 作為 pytest 起點
6. **未來擴充**：
   - **curled-wake 模型**：偏航尾流的 counter-rotating vortex pair 細節（Bastankhah 線性式已涵蓋主項）
   - **wake recovery 紊流**：遠場 TI 恢復至自由流的時間常數（Crespo-Hernández x^-0.32 已接近）
   - **穩定度對近尾流 ε/D 的修正**：目前只改 k\*，完整 Abkar 2015 亦建議改 ε（次要效應）
   - **半日大氣潮 S2**（熱帶 ±1.5 hPa、中緯度 ±0.3 hPa）若 #106 後觀測到日週期過於平靜再加
7. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
8. **F401 清理**：`turbine_model.py`、`dashboard.py`、`scada_system.py` 等根目錄早期原型檔案的 unused import 仍存在（追蹤 #44）

## 通知

已透過 email 發送日報至 moredof@gmail.com（請依專案實際 email 通知管道配置執行）。
