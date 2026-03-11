# Tip-s-Tips
The Web Application to collect some tips which makes your life better.

## functions
tips view

add tip

review tips

## PreView

https://satoyaa.github.io/Tip-s-Tips/

## Setup & 起動方法

### 1. バックエンド（FastAPI + DB）

サーバ起動：

```bash
cd backend
.\venv\Scripts\activate 
uvicorn main:app --reload --port 8000
```

起動すると以下が自動で行われます：
- `backend/DB/tips.db`（SQLite）が自動作成される
- バックグラウンドで楽天レシピAPI → Gemini AI要約 → DB保存が定期実行される

手動でデータ収集する場合：

```bash
# 全キーワード一括収集
curl -X POST http://localhost:8000/api/collect

# 特定キーワードで収集
curl -X POST http://localhost:8000/api/collect/カレー
```

### 2. フロントエンド（React + Vite）

```bash
cd tips-tips
npm run dev
```

`http://localhost:5173` でアクセスできます。`/api` へのリクエストは Vite のプロキシ経由で `http://localhost:8000` に転送されます。
