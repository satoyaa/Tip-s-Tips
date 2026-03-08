from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from datetime import datetime
import random
import uuid
import json
import os

app = FastAPI()

# CORS設定（Reactからのアクセス許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "dbAll.json"

# --- データ構造の定義 ---

# フロントエンドから受け取るデータ（入力が必要なものだけ）
class TipCreate(BaseModel):
    tipTitle: str
    tipExplanation: str

# データベースに保存・取得するデータ（全ての項目）
class Tip(BaseModel):
    id: str
    tipTitle: str
    tipExplanation: str
    mainTags: List[str]
    subTags: List[str]
    source: List[str]
    tipLikes: int
    tipDislikes: int
    upLoadDate: str
    
# フロントエンドに送るデータ（表示用）
class TipDisplay(BaseModel):
    id: str
    tipTitle: str
    tipExplanation: str
    tipTop: int
    tipLeft : int
    tipRotate : float
    source: List[str]
    tipLikes: int
    tipDislikes: int
    upLoadDate: str
    
# 評価更新用のデータ
class LikeUpdate(BaseModel):
    tipLikes: int

# バッチ更新用: { "updates": { "id1": likes1, "id2": likes2, ... } }
class LikesBatchUpdate(BaseModel):
    updates: Dict[str, int]

def read_db() -> List[dict]:
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(data: List[dict]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

#検索表示用のデータ読み込み
@app.get("/tips", response_model=List[TipDisplay])
def get_tips(tag: Optional[str] = Query(None)): # クエリパラメータ 'tag' を定義
    raw_data = read_db()
    
    # 1. バックエンド側でのフィルタリング
    if tag:
        # mainTagsの中に指定された文字列が含まれるものだけを抽出
        filtered_data = [item for item in raw_data if tag in item.get("mainTags", [])]
    else:
        filtered_data = raw_data
    
    # 2. 絞り込み後のリストに対して表示用計算を行う
    display_tips = []
    for index, item in enumerate(filtered_data):
        tip_left = (index * 400) % 1200
        tip_top = (index // 3) * 300
        tip_rotate = (random.random() - 0.5) * 10
        
        display_tips.append(TipDisplay(
            id=item["id"],
            tipTitle=item["tipTitle"],
            tipExplanation=item["tipExplanation"],
            tipTop=tip_top,
            tipLeft=tip_left,
            tipRotate=tip_rotate,
            mainTags=item.get("mainTags", []),
            source=item["source"],
            tipLikes=item["tipLikes"],
            tipDislikes=item["tipDislikes"],
            upLoadDate=item["upLoadDate"]
        ))
        
    return display_tips

#ユーザ投稿の新しいデータの追加
@app.post("/tips", response_model=Tip)
def create_tip(tip_in: TipCreate):
    db = read_db()
    
    # バックエンド側でデータを補間
    new_tip_data = {
        "id": str(uuid.uuid4())[:8], # 重複しないIDを生成（例: "a1b2c3d4"）
        "tipTitle": tip_in.tipTitle,
        "tipExplanation": tip_in.tipExplanation,
        "mainTags": [],      # 初期値は空配列
        "subTags": [],       # 初期値は空配列
        "source": [],        # 初期値は空配列
        "tipLikes": 0,       # 初期値は0
        "tipDislikes": 0,    # 初期値は0
        "upLoadDate": datetime.now().strftime("%Y/%m/%d") # 現在の日付
    }
    
    db.append(new_tip_data)
    write_db(db)
    
    return new_tip_data

#評価に関するデータの更新
@app.patch("/tips/{tip_id}/likes", response_model=Tip)
def update_tip_likes(tip_id: str, update_data: LikeUpdate):
    db = read_db()
    
    # 対象のデータを検索
    target_index = None
    for i, item in enumerate(db):
        if item["id"] == tip_id:
            target_index = i
            break
    
    if target_index is None:
        raise HTTPException(status_code=404, detail="Tip not found")
    
    # データを更新
    db[target_index]["tipLikes"] = update_data.tipLikes
    
    # 保存
    write_db(db)

    return db[target_index]


# 複数tipのいいね数をまとめて更新
@app.patch("/tips/batch-likes")
def update_tips_batch_likes(batch: LikesBatchUpdate):
    db = read_db()
    
    for i, item in enumerate(db):
        if item["id"] in batch.updates:
            item["tipLikes"] = batch.updates[item["id"]]
    
    write_db(db)
    return {"updated": list(batch.updates.keys())}