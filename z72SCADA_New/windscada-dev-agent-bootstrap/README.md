# WindSCADA Dev Agent (Bootstrap)

這是一個示範用的「代理人驅動」專案腳手架，展示如何從 0 開始依照 `agent.md` 規範建立文件與程式碼，並導入 VS Code/CI/測試 紀律。

## 快速開始
```bash
# 建立虛擬環境（可選）
python -m venv .venv && source .venv/bin/activate

# 安裝
pip install -r requirements.txt

# 本機啟動 API（預設 http://127.0.0.1:8000 ）
uvicorn app.main:app --reload
```

## 專案結構
- `project.md`：專案目標、範圍與規範（由代理人維護）
- `roadmap.md`：里程碑
- `todo.md`：任務清單（MoSCoW/相依/驗收）
- `development.log`：每次任務紀錄
- `docs/`：需求萃取（discovery）、啟動工作坊（inception）、ADR
- `.vscode/`：VS Code tasks
- `.github/workflows/ci.yml`：CI
- `app/`：FastAPI 服務與測試

> 範例 MVP：健康檢查、紀錄端點、未來可擴充 OPC UA 資料擷取與警報彙整。
