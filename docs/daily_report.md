# digiWindFarm Daily Report

> 最後更新：2026-05-03（分支 `claude/keen-hopper-uDa3c`）

## 今日 Commit 摘要

本日工作（分支 `claude/keen-hopper-uDa3c`）：

- [7adbb4b] fix: restore WMET_WDirRaw (#119 WVTF regression from #125 cleanup)
  - 還原 #125「重複清理」合併導致的 `WMET_WDirRaw` 標籤遺失（#119 WVTF）
  - 同時清除 #127 合併殘留的 `yaw_skew_rad` / `yaw_skew_cos` / `induction_a_yawed` 三行死碼
  - 差異 +6 / −3 行；2 個檔案：`scada_registry.py` 與 `turbine_physics.py`

歷史延續（前 48 小時）：

- [14292f8] Merge PR #130（#127 杯式風速計 overspeeding bias 文件同步）
- [d49795c] feat: cup-anemometer overspeeding bias (#127, IEC 61400-12-1 Annex H)
- [070de49] Merge PR #126（#125 Glauert γ 修正）
- [b97e98f] feat: Glauert yaw skewed-flow correction on NTF + WVTF (#125)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 後續修補 | #119 / #125 / #127 | 機艙感測器轉換鏈 | 偵測到 #125 cleanup 的進位回歸 + #127 殘留死碼，合併修復；本日無新增 issue |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做（BPFO/BPFI、邊帶、峰值因子/峭度警報已完成） |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest，本次新增 `/tmp/test_wdir_raw_restore.py`（16/16 PASS）可作為 IEC 61400-12-1/2 物理鏈共用 pytest 起點 |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | **核心模組 ruff 從 2 個 F841 → 0 個錯誤**（本日修復） |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**未建立新 issue**（修復內容不需新 issue 追蹤），符合「每次最多 3 個新 issue / 1 個 PR」規則。本日工作主要驅動方向為**回歸修復**（restore the dropped WVTF tag）+ **lint cleanup**，未新增 PR（用戶未要求；fix commit 已 push 至工作分支）。

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
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組重回 0 錯誤 |
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `simulator/physics/turbine_physics.py` | 2026-05-03 | 0 | 無測試套件 | 移除 #127 殘留 3 行死碼（`yaw_skew_rad` / `yaw_skew_cos` / `induction_a_yawed`）；新增 `WMET_WDirRaw` 輸出 dict 項目 |
| `simulator/physics/scada_registry.py` | 2026-05-03 | 0 | 無測試套件 | 還原 `WMET_WDirRaw` ScadaTag 定義（#125 cleanup 誤刪） |
| `simulator/physics/wind_field.py` | 2026-04-27 | 0 | 無測試套件 | 無變更 |
| `simulator/engine.py` | 2026-05-02 | 0 | 無測試套件 | 無變更（#127 過後保持） |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（提供 `aero_out.tsr` / `aero_out.ct` 供 NTF/WVTF 共用） |
| `simulator/physics/yaw_model.py` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 60 個 HTTP 路由 + 1 WebSocket。本日無新增路由。詳見 `README.md` 「Core APIs」章節。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**（修復前 2 個 F841 unused-variable）
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`（修復前 2 個錯誤已清除）
- `python -m py_compile simulator/physics/turbine_physics.py simulator/physics/scada_registry.py` — 通過
- 物理單元自測（`/tmp/test_wdir_raw_restore.py`）— **16 / 16 PASS**：
  - `#119` baseline 完整重現：Region 2 (Ct=0.82, λ=7) → +3.36°；Region 2.5 → +3.10°；Region 3 (Ct=0.30, λ=5) → +1.72°；starting (Ct=0.55, λ=6) → +2.63°；停機 / 不運轉 → 0°
  - `#125` Glauert γ 投影：γ=15° → +3.24°（cos=0.966）；γ=30° → +2.91°（cos=0.866）；γ=45° → +2.37°（cos=0.707）；γ=60° clamps to γ=45°
  - 對稱性 ±15° 一致（cos 偶函數）
  - ±8° clamp（Ct=0.95 / λ=2 → +8°）
  - 360° wrap-around（358° + 3.36° → 1.36°）
  - Ct↑ → bias↑ 單調
  - λ↑ → bias↓ 單調
  - |γ|↑ → bias↓ 單調
- 引擎端到端 smoke test：未執行（本環境未安裝 numpy；獨立物理單元測試已驗證 #119 / #125 / 本次修復邏輯）
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本累積至 4 個（`/tmp/test_ntf.py` / `test_wvtf.py` / `test_glauert_yaw_skew.py` / `test_wdir_raw_restore.py`），可一併移入 `tests/physics/test_iec_61400_12.py` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**104 個**（registry 110 entries = 104 physics + 6 system，恢復至 #119 / #125 後基線）

## 今日修補：WMET_WDirRaw 回歸修復 + #127 殘留死碼清除

### 問題與根因

`#125` 的 commit message 與 daily report 都聲稱「移除 `#119` 合併殘留的 `WMET_WDirRaw` 重複 key」，並標記為 F601 lint 修復。但實際情況：

1. **`scada_registry.py`**：原本就只有**一個** `WMET_WDirRaw` ScadaTag 定義（位於 line 148–152，緊接 `WMET_WDirAbs` 之後），**並無重複**。F601 警告完全來自 `turbine_physics.py::step()` 輸出 dict 內的重複 dict key（`{"WMET_WDirRaw": ..., ..., "WMET_WDirRaw": ...}`，兩處 round/value 不同）。
2. **`#125` cleanup 誤判**：把 `scada_registry.py` 唯一的 `WMET_WDirRaw` 連同 `turbine_physics.py` 的重複 dict key 一起刪掉，於是 SCADA registry 從 110 → 109，且 `WMET_WDirRaw` 從 `step()` 輸出 dict 完全消失。
3. **殘留遺孤**：`step()` 內仍計算 `nac_vane_raw = (wind_direction + vane_bias_deg) % 360.0`（line 778），但因 dict 已無對應 key，這個變數變成「ruff F841 unused variable」；`#119` WVTF 物理仍在跑，但 SCADA 端讀不到，下游消費者拿到 missing-key fallback。

額外地，`#127` 杯式風速計 overspeeding bias 合併時，又留下三行孤立程式碼：

```python
# turbine_physics.py:739-741 (合併殘留)
yaw_skew_rad = math.radians(max(-45.0, min(45.0, yaw_out["yaw_error"])))
yaw_skew_cos = math.cos(yaw_skew_rad)
induction_a_yawed = induction_a * yaw_skew_cos * yaw_skew_cos
```

這三行在 `#125` `cos_gamma` / `cos2_gamma` 區塊（line 725–727）的下方，內容完全等價但變數名不同，且**從未被使用**——active NTF 路徑使用 `cos2_gamma`。ruff F841 抓到 `induction_a_yawed` 與下方的 `nac_vane_raw` 兩個 unused variable。

### 為何這是 IEC 61400-12-2 規範下的物理回歸

`#119` 引入 `WMET_WDirRaw` 是為了完整 IEC 61400-12-1/2 機艙感測器轉換函數鏈：

- `WMET_WSpeedRaw`（`#117` NTF）：杯式 / sonic 風速計受軸向誘導折扣的原始讀值
- `WMET_WDirRaw`（`#119` WVTF）：風向計受轉子尾流旋轉偏置的原始讀值

兩者**配對**才能讓「以機艙風速計與風向計校驗 nacelle power performance」（IEC 61400-12-2 ed.1 §6.4 + Annex E）的下游分析正確進行。`#125` cleanup 把其中一半（風向計）刪掉，等於把 `#119` 的物理工作從 SCADA 端隱藏，但物理計算還在跑（`nac_vane_raw` 還在計算），這是典型的「靜默回歸」（silent regression）。

### 物理依據（重申以記錄完整脈絡）

`#119` 引用的 swirl bias：

```
θ_swirl ≈ Ct / (2·λ) [rad]    (Burton et al. 2011 Wind Energy Handbook §3.7)
                              (源自 BEM tangential induction a' = Ct/(4·λ))
```

`#125` 的 Glauert γ 投影：

```
θ_swirl_eff = (Ct / (2·λ)) · cos(γ)    (planar projection / Burton §3.10)
γ clamped ±45°
```

| 操作狀態 | Ct | λ | γ | bias |
|---------|-----|-----|----|------|
| Region 2 peak Cp | 0.82 | 7 | 0° | +3.36° |
| Region 2 偏航小 | 0.82 | 7 | 15° | +3.24° |
| Region 2 偏航中 | 0.82 | 7 | 30° | +2.91° |
| Region 2 偏航大 | 0.82 | 7 | 45° | +2.37° |
| Region 3 變槳 | 0.30 | 5 | 0° | +1.72° |
| 停機 | — | — | — | 0° |

### 修補範圍

1. `simulator/physics/scada_registry.py`：在 `WMET_WSpeedRaw`（line 193–197）正下方新增 `WMET_WDirRaw` ScadaTag（與 `WMET_WSpeedRaw` 配對，作為 IEC 61400-12-1/2 機艙感測器原始讀值雙生對）。
2. `simulator/physics/turbine_physics.py`：
   - 移除 `#127` 合併殘留的 3 行死碼（`yaw_skew_rad` / `yaw_skew_cos` / `induction_a_yawed`）—— `#125` `cos2_gamma` 已涵蓋
   - 在輸出 dict 新增 `"WMET_WDirRaw": round(nac_vane_raw, 2)`
3. SCADA 物理標籤總數：**104**（不變）；registry total entries：109 → **110**（恢復至 `#119` / `#125` 後基線 = 104 physics + 6 system）

### 驗證結果

`/tmp/test_wdir_raw_restore.py`（16 / 16 PASS）：

| 案例 | 預期 | 實際 |
|------|------|------|
| R2 baseline γ=0° | 3.36° | 3.356° ✓ |
| R2.5 baseline γ=0° | 3.10° | 3.104° ✓ |
| R3 baseline γ=0° | 1.72° | 1.719° ✓ |
| starting γ=0° | 2.63° | 2.626° ✓ |
| stopped (rpm=0) | 0° | 0° ✓ |
| not running | 0° | 0° ✓ |
| 極端 Ct=0.95/λ=2 clamp +8° | 8.00° | 8.000° ✓ |
| R2 γ=15° | 3.24° | 3.242° ✓ |
| R2 γ=30° | 2.91° | 2.906° ✓ |
| R2 γ=45° | 2.37° | 2.373° ✓ |
| γ=60° clamp 至 45° | 2.37° | 2.373° ✓ |
| ±15° 對稱性 | 3.24° | 3.242° ✓ |
| 360° wrap (358°+3.36°→1.36°) | 1.36° | 1.356° ✓ |
| Ct↑ → bias↑ 單調 | ✓ | ✓ |
| λ↑ → bias↓ 單調 | ✓ | ✓ |
| \|γ\|↑ → bias↓ 單調 | ✓ | ✓ |

### 為何不是新功能而是修補（符合工作原則）

- 「prefer changing physical causes over directly offsetting output tags」：本次只是還原 `#119` 引入的物理「因」（轉子尾流旋轉 → 風向計偏移）讓 SCADA 端讀得到，並未引入新公式
- 「keep new work observable in history charts whenever possible」：恢復 `WMET_WDirRaw` 後，前端 history、API export、OPC adapter 才能再次觀察 `(WMET_WDirRaw − WMET_WDirAbs)` 通道，這是工程現場診斷「vane miscalibration → 系統性偏航誤差」的關鍵訊號
- 不引入新 RNG mutation、新狀態變數、新計算成本——`nac_vane_raw` 早已計算，只是把它接回輸出
- 與既有 `#125` Glauert γ 修正 **零衝突**——`vane_bias_deg` 計算（line 772–777）已包含 `cos_gamma`

### 與其他模型的關係

- `power_curve.py`：提供 `aero_out.ct` / `aero_out.tsr`（不變）
- `yaw_model.py`：提供 `yaw_out["yaw_error"]`（不變）
- `wind_field.py`：`WMET_WDirAbs`（自由流方向）保持不變，繼續被上游 wake 索引與 yaw 控制器使用
- `frontend/`：可在 settings tags 列表新增 `WMET_WDirRaw`（不必要，因為 OPC adapter 與 API export 都會自動反映 registry）

## 建議行動

1. **物理鏈路下一步**（保留 `#125` 日報所述 6 項候選）：`#119` / `#125` / `#127` 的 IEC 61400-12-1/2 機艙感測器鏈現已完整閉合，可繼續：
   - 低空噴流 (Low-Level Jet, LLJ)：Taiwan 離岸風場常見現象，與 `#99` 穩定度耦合
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應）
   - 海面波浪 × 風速耦合（離岸場景：風浪互動、海面粗糙度動態變化 z₀(U)）
   - 風速計 1P / 3P 高頻擾動（葉片通過機艙頂部的機械擾動）—— 補完 `#117` 的時間域訊號真實性
   - 動態尾流捲曲 (curled-wake)：偏航 + Ct 大角度下的 counter-rotating vortex pair，補完 `#97` Bastankhah 線性偏轉
   - 氣動彈性簡化 BEM（葉素動量法），取代目前 Cp(λ,β) 解析面
2. **測試基礎建設（#52）**：累積到 4 個 `/tmp/` IEC 61400-12-1/2 物理單元測試（NTF / WVTF / Glauert / WDirRaw 回歸），可移入 `tests/physics/test_iec_61400_12.py` 作為 pytest 起點，再涵蓋 `#99` / `#109` / `#111` / `#113` / `#115` / `#117` / `#119` / `#125` / `#127` 共九個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
4. **PR review 流程改善**：`#125` 與 `#127` 兩次合併都留下「靜默」殘留（一次刪光必要 tag、一次留死碼），建議未來在 PR 階段加上「`ruff check simulator/` 必須 pass」的 CI gate，可在 5 分鐘內捕獲今日修復的兩種 F841 問題。
