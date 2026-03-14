from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from datetime import datetime
import random
import uuid
import ctypes
from sqlalchemy.orm import Session
import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS設定（Reactからのアクセス許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 本番環境ではCloudFrontのURLを指定する
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    subTags: List[str]
    tipTop: float
    tipLeft : float
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
    
#C言語に突っ込む用
class DataPoint(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("tags", (ctypes.c_char * 64) * 3),  
        ("rotate", ctypes.c_double)
    ]
    
#タグリスト
tag_list = ["焼き方", "ゆで方", "煮詰め方", "揚げ方", "切り方", "味付け"]

#C言語ライブラリの読込
#lib = ctypes.CDLL('./libGA2.dll') #Windows向け
lib = ctypes.CDLL('./libGA.so') #Linux向け
TagListType = (ctypes.c_char * 64) * 100
"""
lib.ga_main.argtypes = [
    ctypes.POINTER(DataPoint), # DataItem* dataset
    ctypes.c_int,             # int n
    TagListType,
    ctypes.c_int,
]
"""

#C言語向け入力への変換用の関数
def convert_tips_to_c_array(display_tips):
    # 必要な要素数を持つC配列の型を動的に定義
    num_tips = len(display_tips)
    DataPointArray = DataPoint * num_tips
    
    # 配列のインスタンスを作成
    c_array = DataPointArray()

    for i, tip in enumerate(display_tips):
        # 評価計算に必要な座標と回転角だけを抽出してマッピング
        # (tipLeft -> x, tipTop -> y)
        c_array[i].x = tip.tipLeft
        c_array[i].y = tip.tipTop
        c_array[i].rotate = tip.tipRotate
        
        # タグの変換処理
        for j, tag in enumerate(tip.subTags):
            if j >= 3:
                break  # C側の配列サイズが3までのため、4つ以上のタグは除外
            
            # 日本語タグに対応するため UTF-8 のバイト列に変換して代入
            c_array[i].tags[j].value = tag.encode('utf-8')
            
            
    return c_array, num_tips

#C言語の入力に適した形への変換
def convert_tags_to_c_array(tag_list, max_byte_length=64):
    num_tags = len(tag_list)
    
    # C言語の型「char[max_byte_length]」と「char[要素数][max_byte_length]」を動的に定義
    TagStringType = ctypes.c_char * max_byte_length
    TagListType = TagStringType * num_tags
    
    # ctypes の配列インスタンスを作成
    c_tag_array = TagListType()
    
    for i, tag in enumerate(tag_list):
        # バイト列に変換して代入 (.value を使うのが正しい書き方です)
        c_tag_array[i].value = tag.encode('utf-8')
        
    return c_tag_array, num_tags

#検索表示用のデータ読み込み
@app.get("/tips", response_model=List[TipDisplay])
def get_tips(tag: Optional[str] = Query(None), db: Session = Depends(get_db)): # クエリパラメータ 'tag' を定義
    query = db.query(models.TipsDatabase)
    
    # 1. バックエンド側でのフィルタリング
    if tag:
        # mainTagsの中に指定された文字列が含まれるものだけを抽出
        query = query.filter(models.TipsDatabase.mainTags.astext.ilike(f'%"{tag}"%'))
    
    filtered_data = query.all()
    
    # 2. 絞り込み後のリストに対して表示用計算を行う
    display_tips = []
    for item in filtered_data:
        tip_rotate = (random.random() - 0.5) * 10
        
        display_tips.append(TipDisplay(
            id=item.id,
            tipTitle=item.tipTitle,
            tipExplanation=item.tipExplanation,
            tipTop=0.0,
            tipLeft=0.0,
            tipRotate=tip_rotate,
            subTags=item.subTags,
            source=item.source,
            tipLikes=item.tipLikes,
            tipDislikes=item.tipDislikes,
            upLoadDate=item.upLoadDate
        ))
        
    c_array, num_tips = convert_tips_to_c_array(display_tips)
    c_tag_array, num_tags = convert_tags_to_c_array(tag_list)
    lib.ga_main(c_array, num_tips, c_tag_array, num_tags)
    #for i in range(5):
    #    print(f"Python-side: Updated Data[{i}] ({c_array[i].x}, {c_array[i].y})")
    for i in range(num_tips):
        display_tips[i].tipLeft = c_array[i].x
        display_tips[i].tipTop = c_array[i].y
    return display_tips

#ユーザ投稿の新しいデータの追加
@app.post("/tips", response_model=Tip)
def create_tip(tip_in: TipCreate, db: Session = Depends(get_db)):
    # バックエンド側でデータを補間
    new_tip = models.TipsDatabase(
        id=str(uuid.uuid4())[:8],  # 重複しないIDを生成（例: "a1b2c3d4"）
        tipTitle=tip_in.tipTitle,
        tipExplanation=tip_in.tipExplanation,
        mainTags=[],      # 初期値は空配列
        subTags=[],       # 初期値は空配列
        source=[],        # 初期値は空配列
        tipLikes=0,       # 初期値は0
        tipDislikes=0,    # 初期値は0
        upLoadDate=datetime.now().strftime("%Y/%m/%d") # 現在の日付
    )
    
    db.add(new_tip)
    db.commit()
    db.refresh(new_tip)
    
    return {
        "id": new_tip.id,
        "tipTitle": new_tip.tipTitle,
        "tipExplanation": new_tip.tipExplanation,
        "mainTags": new_tip.mainTags,
        "subTags": new_tip.subTags,
        "source": new_tip.source,
        "tipLikes": new_tip.tipLikes,
        "tipDislikes": new_tip.tipDislikes,
        "upLoadDate": new_tip.upLoadDate
    }

#評価に関するデータの更新
@app.patch("/tips/{tip_id}/likes", response_model=Tip)
def update_tip_likes(tip_id: str, update_data: LikeUpdate, db: Session = Depends(get_db)):
    tip = db.query(models.TipsDatabase).filter(models.TipsDatabase.id == tip_id).first()
    
    if not tip:
        raise HTTPException(status_code=404, detail="Tip not found")
    
    # データを更新
    tip.tipLikes = update_data.tipLikes
    db.commit()
    db.refresh(tip)

    return {
        "id": tip.id,
        "tipTitle": tip.tipTitle,
        "tipExplanation": tip.tipExplanation,
        "mainTags": tip.mainTags,
        "subTags": tip.subTags,
        "source": tip.source,
        "tipLikes": tip.tipLikes,
        "tipDislikes": tip.tipDislikes,
        "upLoadDate": tip.upLoadDate
    }


# 複数tipのいいね数をまとめて更新
@app.patch("/tips/batch-likes")
def update_tips_batch_likes(batch: LikesBatchUpdate, db: Session = Depends(get_db)):
    for tip_id, likes_count in batch.updates.items():
        tip = db.query(models.TipsDatabase).filter(models.TipsDatabase.id == tip_id).first()
        if tip:
            tip.tipLikes = likes_count
    
    db.commit()
    return {"updated": list(batch.updates.keys())}