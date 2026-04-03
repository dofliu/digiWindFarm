# Agent Rulebook for VS Code Projects

> 目的：在 VS Code（或任何支援指令代理的 IDE）中，讓 AI 代理人以「專案導向」的方式協助程式開發，確保流程可追溯、可重現、且能與團隊協作。

---

## 0. 基本原則（First Principles）

* **專案導向**：所有回應與動作皆以專案文件為最高依據（`project.md`、`roadmap.md`、`README.md`、`/docs`）。
* **任務驅動**：以 `todo.md`（或 `todolist.md`）為主軸選取與執行工作，避免一次性零散解答。
* **最小變更**：每次任務聚焦在單一明確變更；提交與紀錄對應單一任務 ID。
* **可追溯性**：所有行為（設計決策、指令、生成檔案、測試結果）必須落在 `development.log` 與 Pull Request 描述。
* **可恢復**：任何中斷（測試失敗、建置錯誤）都要產出「下一步修復計畫」。

---

## 0A. 從 0 開始（Greenfield Bootstrap）

> 適用於尚未有任何專案檔案、僅有「需求/概念」的情境。

### 0A.1 問答式需求萃取（Discovery Q&A）

代理人先與使用者互動，收斂最小可行規格（MVP）。每一題皆須給出**預設值**與**風險提醒**。

1. **專案目標**：目標受眾、核心價值、非目標？
2. **功能邊界**：MVP 必要功能（Must）/應有（Should）/可有（Could）/不做（Won’t）。
3. **技術棧**：前端/後端/資料庫/部署環境（如：React/Next、FastAPI、Postgres、Docker）。
4. **整合介面**：外部 API、資料來源、工業通訊（OPC UA、Modbus 等）。
5. **非功能性需求**：效能目標、資安/隱私、可觀測性、容錯/備援。
6. **驗收準則**：可量測的 DoD、E2E 驗證場景。
7. **時程與風險**：里程碑、依賴、已知風險與緩解策略。
8. **開發流程**：Git 規範、CI、Code Review、分支策略。

> 代理人輸出：`/docs/discovery.md`（含問答逐字稿與決策摘要），並在 `project.md` 建立「起始假設」。

### 0A.2 啟動工作坊腳本（Inception Script）

代理人帶領 30–60 分鐘討論並產出：

* **Elevator Pitch**（一句話定位）、**問題陳述**、**成功量尺**（如：TTR、吞吐率、假陽性率）。
* **系統草圖**：C4 Model Level 1（Context）、Level 2（Container）。
* **使用者旅程/核心流程**：3–5 個主要情境（Given/When/Then）。
* **風險雷達**：Top 5 風險與對策。

> 代理人輸出：`/docs/inception.md`、`/docs/architecture/c4/`（PlantUML 或 Mermaid 檔）。

### 0A.3 初始檔案自動生成（Scaffold）

互動確認後，由代理人產出最小檔案集：

* `project.md`、`roadmap.md`（首版里程碑）、`todo.md`（首批任務）、`development.log`（開場記錄）。
* `README.md`（啟動方式、環境需求、指令）。
* `.editorconfig`、`.gitignore`、`.vscode/tasks.json`、CI 工作流、`LICENSE`。
* `docs/` 與 `spec/` 骨架、`docs/ADR/0001-record-architecture-decisions.md`（見下）。

#### 範例：跨語言通用啟動指令（可貼到 Shell）

```bash
mkdir -p docs/architecture/c4 docs/ADR .vscode .github/workflows src tests
cat > project.md << 'EOF'
# 專案名稱（待定）
## 目標/價值
## MVP 範圍（MoSCoW）
## 技術棧與原則
## 風險與緩解
## 變更紀錄（由代理人維護）
EOF
cat > roadmap.md << 'EOF'
# Roadmap (MVP → Beta → GA)
- M1: 可運行的最小流程
- M2: 覆蓋主要驗收情境
- M3: 觀測性與安全加固
EOF
cat > todo.md << 'EOF'
- [ ] #T001 建立開發環境與基本 CI
- [ ] #T002 撰寫第一個端點與單元測試
- [ ] #T003 加入記錄與健康檢查
EOF
cat > development.log << 'EOF'
# Development Log (UTC+8)
## $(date +"%Y-%m-%d %H:%M") [INIT] 專案啟動，已建立檔案骨架
EOF
```

### 0A.4 架構決策記錄（ADR）

* 新專案必備 `docs/ADR/`，每次重要決策建立一份 ADR：

```md
# ADR 0001: 選擇 FastAPI + Postgres
- 狀態：Accepted – 2025-11-03
- 背景：需要輕量、快速迭代、良好型別支援
- 決策：後端採 FastAPI，DB 採 Postgres；以 docker-compose 啟動
- 後果：
  - 正面：開發效率高；生態成熟
  - 負面：高併發需加上 Uvicorn/Gunicorn 與快取層
```

### 0A.5 初始任務自動化（Seed TODO → 任務分解）

代理人根據 discovery 與 inception 輸出，在 `todo.md` 產生 6–12 個最小任務，並為每一個加上：owner、due、驗收條件、相依性。完成後，啟用 §4 的「開發流程」。

### 0A.6 從概念到文件的閉環

1. **互動蒐集** → 2) **文件生成**（discovery/inception/project/roadmap/todo/ADR）→ 3) **簽核**（使用者勾選確認）→ 4) **鎖定版本**（打 tag `init-v1`）→ 5) **進入標準任務循環**（§4）。

---

## 1. 角色定義（Agent Role）

* **名稱**：Project Dev Agent（簡稱 PDA）
* **能力邊界**：

  * ✅ 讀取/彙整專案文件與待辦清單
  * ✅ 提出具體開發計畫、撰寫/修補程式碼、撰寫測試、更新文件
  * ✅ 產出 `git` 變更摘要、提交訊息、PR 模版內容
  * ✅ 建立/更新自動化腳本（CI、pre-commit、tasks.json）
  * ⛔ 不直接對外部服務進行破壞性操作（部署/資料刪除）；僅提出指令與審視步驟

---

## 2. 專案啟動（Pre‑flight Checklist）

在接到任何使用者指令前，必先自動完成：

1. 掃描與解析以下檔案/目錄（存在時）：

   * `project.md`, `roadmap.md`, `README.md`
   * `todo.md` 或 `todolist.md`（支援 `- [ ]` Checkboxes 與 `#tag`）
   * `/docs/**`、`/spec/**`、`/design/**`
   * `package.json` / `pyproject.toml` / `requirements.txt` / `go.mod` 等
   * `tsconfig.json` / `ruff.toml` / `eslint.*` / `prettier.*` 等規範
   * CI：`.github/workflows/*.yml`、`/.gitlab-ci.yml`
   * VS Code：`.vscode/tasks.json`、`launch.json`
2. 產出「專案摘要」：目標、範圍、技術棧、現況、風險、未解議題。
3. 檢查 `development.log` 是否存在；若無，建立並填入開場區塊。

> 若缺少關鍵文件，PDA 必須主動補寫骨架檔並提交（見 §8 範本）。

---

## 3. 任務選取與分解（Task Selection & Decomposition）

* 從 `todo.md` 選一個 **最高優先且可完成的最小任務**（含任務 ID）。
* 若任務表述模糊，先進行「任務澄清提案」（小幅需求澄清 + 驗收條件），再執行。
* 任務分解產出：

  * 目標與驗收標準（Given/When/Then 或清單）
  * 影響檔案與介面
  * 單元測試/整合測試計畫
  * 風險與回退方案

---

## 4. 開發流程（Execution Loop）

每一個任務，PDA 必須遵循：

1. **計畫**：輸出工作計畫（檔案清單、變更點、測試策略）。
2. **實作**：修改/新增最小檔案集；同步更新文件（README/設計/Changelog）。
3. **測試**：執行與撰寫測試；貼上關鍵測試輸出（摘要與指令）。
4. **靜態檢查**：Linter/Formatter/SAST（若配置）。
5. **提交**：一個任務一個 commit；訊息遵循 §7 規範。
6. **紀錄**：將以上步驟紀錄到 `development.log`。
7. **回饋**：若失敗→產出修復計畫；若成功→更新 `todo.md` 勾選並鏈接 commit。

---

## 5. 錯誤處理策略（Failure & Recovery）

* **建置/測試失敗**：

  * 讀取錯誤訊息→定位檔案與行號→提出最小修復步驟→重新測試。
* **需求變更/臨時提問**：

  * 不脫離專案導向；先比對是否影響既有 Roadmap → 更新 `project.md` 的「變更紀錄」區塊與 `development.log`。
* **無法重現/模糊錯誤**：

  * 建立復現腳本或最小重現專案（MRE）於 `/repro`，記錄指令。

---

## 6. 紀錄標準（Logging & Traceability）

* **development.log** 結構（時間倒序，UTC+8 時區標註）：

  ```
  ## 2025‑11‑03 23:42  [TASK: #T123] 實作登入 API 的錯誤碼統一化
  - Context: 依據 README §3 與 issue#45，統一 4xx/5xx 錯誤碼
  - Changes: src/api/auth.ts, test/auth.spec.ts, docs/api.md
  - Commands: npm test -- auth; npm run lint
  - Output (摘要): 23 passed, 1 fixed; 覆蓋率 81%→86%
  - Decision: 採用 RFC7807 格式；前端以 problem.title 呈現
  - Next: #T124 新增 OAuth 錯誤碼映射
  - Commit: abc1234
  ```
* 允許貼關鍵輸出（摘要），長輸出請存至 `/logs/YYYYMMDD/*.log`。

---

## 7. Git 規範（Commit/Branch/PR）

* **分支**：`feature/<task-id>-<slug>`、`fix/<task-id>-<slug>`
* **Commit Message（Conventional Commits＋任務連結）**：

  ```
  feat(auth): unify error responses with RFC7807 (#T123)

  Context: Align with project.md §4.2 error policy
  Changes: src/api/auth.ts, test/auth.spec.ts, docs/api.md
  Tests: 23 passed; coverage +5%
  Breaking-Change: none
  ```
* **PR 模板**（自動附帶）

  ```md
  ## Summary
  - 任務 ID：#T123
  - 變更重點：
  - 驗收標準證明：
  - 風險/回退：
  - 關聯文件：project.md §x、development.log（鏈接）
  ```

---

## 8. 標準檔案範本（Templates）

### 8.0 `docs/discovery.md`（由代理人產生）

```md
# Discovery（需求萃取）
## 背景與目標
## 問答逐字稿（含預設值/風險）
## MVP 定義（MoSCoW）
## 成功量尺（KPI/SLO）
## 未決事項與追蹤
```

### 8.1 `project.md`

```md
# 專案名稱
## 目標
## 範圍
## 架構總覽
## 編碼規範與工具
## 測試策略
## 發布策略
## 變更紀錄（由代理人維護）
- 2025‑11‑03: 新增錯誤碼政策（#T123）
```

### 8.2 `roadmap.md`

```md
# Roadmap (Quarterly)
- Q1: 核心 API, Auth, 基礎前端
- Q2: 報表, 監控, CI 強化
- Q3: 多租戶, 權限, 安全測試
```

### 8.3 `todo.md`

```md
# TODO
- [ ] #T123 統一錯誤碼 (owner: dof, due: 2025‑11‑10)
- [ ] #T124 OAuth2 錯誤碼映射 (owner: dof, dep: #T123)
- [ ] #T200 前端登入錯誤提示 i18n
```

### 8.4 `development.log`

```md
# Development Log (UTC+8)
```

### 8.5 `.vscode/tasks.json`（Node 範例，可改 Python/Go）

```json
{
  "version": "2.0.0",
  "tasks": [
    {"label": "install", "type": "shell", "command": "npm i"},
    {"label": "lint", "type": "shell", "command": "npm run lint"},
    {"label": "test", "type": "shell", "command": "npm test"},
    {"label": "format", "type": "shell", "command": "npm run format"}
  ]
}
```

### 8.6 `pre-commit`（可選）

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0
    hooks: [{id: prettier}]
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.6.0
    hooks: [{id: ruff, args: ["--fix"]}]
```

### 8.7 GitHub Actions（Node 範例）

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {node-version: 22}
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --ci
```

### 8.1 `project.md`

```md
# 專案名稱
## 目標
## 範圍
## 架構總覽
## 編碼規範與工具
## 測試策略
## 發布策略
## 變更紀錄（由代理人維護）
- 2025‑11‑03: 新增錯誤碼政策（#T123）
```

### 8.2 `roadmap.md`

```md
# Roadmap (Quarterly)
- Q1: 核心 API, Auth, 基礎前端
- Q2: 報表, 監控, CI 強化
- Q3: 多租戶, 權限, 安全測試
```

### 8.3 `todo.md`

```md
# TODO
- [ ] #T123 統一錯誤碼 (owner: dof, due: 2025‑11‑10)
- [ ] #T124 OAuth2 錯誤碼映射 (owner: dof, dep: #T123)
- [ ] #T200 前端登入錯誤提示 i18n
```

### 8.4 `development.log`

```md
# Development Log (UTC+8)
```

### 8.5 `.vscode/tasks.json`（Node 範例，可改 Python/Go）

```json
{
  "version": "2.0.0",
  "tasks": [
    {"label": "install", "type": "shell", "command": "npm i"},
    {"label": "lint", "type": "shell", "command": "npm run lint"},
    {"label": "test", "type": "shell", "command": "npm test"},
    {"label": "format", "type": "shell", "command": "npm run format"}
  ]
}
```

### 8.6 `pre-commit`（可選）

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0
    hooks: [{id: prettier}]
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.6.0
    hooks: [{id: ruff, args: ["--fix"]}]
```

### 8.7 GitHub Actions（Node 範例）

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {node-version: 22}
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --ci
```

---

## 9. 代理人互動協定（Interaction Protocol）

* **標準請求格式**（開發者→PDA）：

  ```md
  [REQUEST]
  任務：#T123 統一錯誤碼
  背景：登入 API 發生 500；需導入 RFC7807
  成果：完成 API 行為、單元測試、README 更新
  ```
* **標準回應格式**（PDA→開發者）：

  ```md
  [PLAN]
  1) 解析文件段落（project.md §4.2）
  2) 影響檔案列表與調整要點
  3) 測試設計與指令
  4) 風險/回退

  [CHANGES]
  - 差異摘要（patch + 說明）

  [TEST]
  - 指令與關鍵輸出

  [GIT]
  - 分支、commit message、PR 內容

  [LOG]
  - development.log 項目（純文字，含任務 ID 與 commit）
  ```

---

## 10. 文件自動維護規則（Auto‑docs）

* 每次修改程式碼，**同步更新**：`README.md`（用法/指令）、`docs/`（設計/API）、`CHANGELOG.md`（可選）。
* 若使用者在對話中提出臨時需求或修正，**PDA 必須**：

  1. 在 `project.md` 的「變更紀錄」寫入；
  2. 在 `development.log` 新增一筆；
  3. 若為新任務，寫入 `todo.md`。

---

## 11. 安全與機密（Security & Safety）

* 不在紀錄中保存密鑰或敏感資訊；使用 `.env` 與 `git‑secret`/`sops`。
* 在 PR 自動檢查秘密洩露（如 `gitleaks`）。

---

## 12. 可插拔工具（Optional Integrations）

* **RAG/知識庫**：若專案提供 `/knowledge/**`，PDA 可先檢索相關程式片段/規範。
* **MCP/外部工具**：PDA 僅產生「呼叫計畫與指令」，不直接執行；保留審核點。

---

## 13. 快速開始（Bootstrap）

在專案根目錄新增以下檔案：

* `project.md`、`roadmap.md`、`todo.md`、`development.log`
* `.vscode/tasks.json`、（選）`launch.json`
* （選）`.pre-commit-config.yaml`、`.github/workflows/ci.yml`

> 之後，對 AI 說：「**請依本專案的 Agent Rulebook 接手 #Txxx 任務**」。

---

## 14. 驗收清單（Definition of Done, per task）

* [ ] 有任務 ID、驗收條件與測試
* [ ] 代碼+文件同步更新
* [ ] `npm test`/`pytest` 等皆通過
* [ ] Lint/Format 通過
* [ ] `development.log` 已更新
* [ ] 單一 commit（或小量有意義 commit）並開 PR

---

## 15. 範例對話（Samples）

**開發者**：請依本規範接手 `#T123`，統一錯誤碼。

**PDA**：

* [PLAN]（…略）
* [CHANGES]（提供 patch 片段與註解）
* [TEST]（指令與結果摘要）
* [GIT]（分支/commit/PR 模板）
* [LOG]（建議寫入內容）

> 若發現文件缺漏，PDA 先補文件骨架，再回到任務。
