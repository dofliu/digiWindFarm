# ADR 0001: 技術選型 – FastAPI + pytest
- 狀態：Accepted – 2025-11-02
- 背景：MVP 需快速起步、良好型別、可測試
- 決策：後端採 FastAPI，測試採 pytest；CI 使用 GitHub Actions
- 後果：
  - 正面：啟動快、學習曲線平滑
  - 代價：高併發需額外最佳化（之後引入快取/DB/任務佇列）
