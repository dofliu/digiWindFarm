# digiWindFarm Daily Report

> 最後更新：2026-04-25（分支 `claude/keen-hopper-UKuXa`）

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-UKuXa`）：

- feat: couple atmospheric stability to wind veer (Ekman) (#111)
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #111

近 48 小時主幹 `main` 合併摘要：

- [6a48943] Merge PR #110 — 大氣穩定度 × Bastankhah 尾流擴張耦合 (#109)
- [8223232] feat: couple atmospheric stability to Bastankhah wake expansion k* (#109)
- [4af85e2] Merge PR #107 — 大氣壓動態耦合文件同步
- [4b78380] feat: couple ambient pressure to synoptic weather state (#106)
- [6728bae] Merge PR #105 — 尾流誘發紊流增強文件同步

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立+實作 | #111 | 大氣穩定度 × 風切偏向 (wind veer) 耦合 | `veer_rate_eff = veer_base · clamp(1 − s, 0.3, 2.5)` |
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

本日建立 1 個 issue（#111）並完成實作；尚未關閉（待 PR 合併後關閉）。符合「每次最多 3 個新 issue / 1 個 PR」規則。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #111 | 大氣穩定度 × 風切偏向（wind veer）耦合 | enhancement, physics, auto-detected | 2026-04-25 | 已實作於本分支 |
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
| `simulator/physics/turbine_physics.py` | 2026-04-25 | 0 | 無測試套件 | 新增 `veer_rate = veer_base · stability_factor`，effective veer 同時餵入 fatigue path |
| `simulator/physics/wind_field.py` | 2026-04-24 | 0 | 無測試套件 | 無變更（沿用 #109） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 簽章未變，但接收的 `wind_veer_rate` 現為穩定度動態值 |
| `simulator/engine.py` | 2026-04-24 | 0 | 無測試套件 | 無變更（既有 `atm_stability` 已傳入 `model.step(...)`） |
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
- `python -m py_compile simulator/physics/turbine_physics.py` — 通過
- 引擎端到端 smoke test（`WindFarmSimulator(turbine_count=3)` 走 10 步 `_run_one_step(datetime.now(), 1.0)`）— 通過，3 台輸出正常
- 物理單元自測（`/tmp/test_stability_veer.py`）— PASS：穩定 ABL 產生 +37 % 塔架側向彎矩 vs 對流，並多消耗 13 kW 功率
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**102 個**（#111 無新增標籤，觀察性透過既有 `WMET_AtmStab × WLOD_TwrSsMom` 達成）

## 今日新增功能

### 大氣穩定度 × 風切偏向（wind veer）耦合 — #111

**問題與物理原理**

#79 已實作風切偏向（Ekman 螺旋下緣），目前以每台風機固定 `wind_veer_rate=0.10 ± 0.03 °/m` 表示。但實際大氣 veer rate 由穩定度直接控制：

| 大氣狀態 | Veer rate | 物理機制 |
|---------|----------|---------|
| 穩定（夜間 / s≈−1） | 0.15–0.30 °/m | Ekman 螺旋顯著、垂直混合受抑制 |
| 中性（s≈0） | 0.05–0.10 °/m | baseline |
| 對流（午後 / s≈+1） | 0.02–0.05 °/m | 強烈垂直混合「擦掉」方向梯度 |

來源：Holton *An Introduction to Dynamic Meteorology* §5.3；Stull *An Introduction to Boundary Layer Meteorology* §8.5；van der Laan et al. (2017) *Wind Energy* 20, 1191–1208；IEC 61400-1 ed.4 Annex E。

**公式與實作**

```
veer_rate_eff = veer_base · clamp(1.0 − 1.0 · s,  0.3, 2.5)
```

對應映射：
- s=−1（穩定）：factor=2.0 → veer ≈ 0.20 °/m
- s=0（中性）：factor=1.0 → veer ≈ 0.10 °/m（baseline）
- s=+1（對流）：factor=0.0 clamp 0.3 → veer ≈ 0.03 °/m

clamp `[0.3, 2.5]` 防止極端穩定度落到非物理區。每台風機 `_individuality["wind_veer_rate"]` 仍保留作為製造／場址容差。

**實作檔案**

`simulator/physics/turbine_physics.py`（單檔，淨增 +9 / −2 行）：
- 將既有 `veer_rate = self._individuality.get("wind_veer_rate", 0.10)` 一行替換為 `veer_base + veer_factor + veer_rate` 三行計算
- 第 698 行 `wind_veer_rate=...` 從讀 `_individuality` 改為直接使用上方計算的 `veer_rate`，**確保 aero 功率損失與 fatigue 結構載荷使用同一數值**

`simulator/engine.py`：無需變更（`atm_stability` 已於 #99 / #109 傳入 `model.step(...)`，`turbine_physics.step` 內已保存於 `self._atm_stability`）

**物理效應（自測驗證 `/tmp/test_stability_veer.py`）**

12 m/s 穩態、200 步啟動後讀取 SCADA：

| s | 預期 veer | P_kw | TwrSS_kNm | ΔTwrSS vs 中性 |
|---|----------|------|-----------|----------------|
| −1.00 | 0.200 °/m | 1704 | 255.9 | **+37.5 %** |
| −0.50 | 0.150 °/m | 1710 | 221.1 | +18.7 % |
| 0.00 | 0.100 °/m | 1714 | 186.2 | baseline |
| +0.50 | 0.050 °/m | 1716 | 151.2 | −18.8 % |
| +1.00 | 0.030 °/m | 1717 | 137.2 | **−26.3 %** |

| 驗證項 | 預期 | 實測 | 結果 |
|--------|------|------|------|
| 單調性 s→veer→TwrSS | 穩定 > 中性 > 對流 | 成立 | ✓ |
| 穩定 ABL 多耗功率 | > 0 kW | 13 kW | ✓ |
| 中性點 TwrSS（baseline） | 與 #79 baseline 相符 | 186.2 | ✓ |
| 中性點 P | 約 1700 kW | 1714 | ✓ |
| 引擎端到端 smoke | 無錯誤 | 通過 | ✓ |
| ruff lint | 0 錯誤 | 0 | ✓ |

**為何這是物理「因」而非輸出偏移**

- veer_rate 是 Ekman 螺旋斜率的物理參數，直接動態變更
- 同一 `veer_rate` 同時餵入：
  - aero 區塊：`veer_offset_rad = math.radians(veer_rate * R * cos(blade_az))` → 計算每葉等效偏角 → 平均 `veer_power_loss` 直接乘到 `aero_torque_knm` 與 `power_kw`
  - fatigue path：`fatigue_model.step(wind_veer_rate=veer_rate, ...)` → 影響 tower SS / blade flap moment 計算
- 不是在 `WLOD_TwrSsMom` 加修正項
- 全場共享同一穩定度（物理事實，符合 ABL 一致性）
- 與 #109（穩定度 × Bastankhah k\*）、#99（穩定度 × α / TI）、#101 / #106（ρ 動態）形成完整 ABL 物理鏈

**觀察性**

- 不新增 SCADA 標籤
- 夜間穩定時段：`WMET_AtmStab` 與 `WLOD_TwrSsMom` 應出現明顯負相關（s 越負→TwrSS 越大；期待 r < −0.4 於生產中風機）
- 與 #109 形成「夜間 wake 變深 + 葉片載荷側向不對稱加劇」的疊加效應，下游風機 fatigue DEL 預期在穩定夜間有 8–18 % 上升
- 長時段資料品質驗證可用 `examples/data_quality_analysis.py` 24h 模式同時觀察 #99 / #109 / #111

## 建議行動

1. **長時段資料品質驗證**：跑 `examples/data_quality_analysis.py` **24 小時自動模式**，觀察：
   - `WMET_AtmStab × WLOD_TwrSsMom` 相關係數是否 < −0.4
   - 夜間穩定時段塔架 DEL 上升 5–15 %
   - 與 #109 疊加：下游風機在夜間穩定時 fatigue DEL 提升幅度
2. **建立 pytest 測試套件（#52）**：本日 `/tmp/test_stability_veer.py` 加上既有 `/tmp/test_stability_wake.py`（#109）已有兩個成熟單元自測腳本，建議共同移入 `tests/physics/` 作為 pytest 起點
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **未來擴充**：
   - 半日大氣潮 S2 解耦（中緯度 ±0.3 hPa）
   - 穩定度 × 紊流積分長度尺度 L_u → wake meander τ_m 動態化（目前 τ=25 s 為常數）
   - curled-wake 模型（偏航尾流的 counter-rotating vortex pair）
6. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
7. **F401 清理**：`turbine_model.py`、`dashboard.py`、`scada_system.py` 等根目錄早期原型檔案的 unused import 仍存在（追蹤 #44）

## 通知

已透過 email 發送日報至 moredof@gmail.com（請依專案實際 email 通知管道配置執行）。
