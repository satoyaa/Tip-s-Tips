from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import random
import uuid
import json
import os
import ctypes

import httpx
from dotenv import load_dotenv

load_dotenv()

from collector import collect_all_recipes, collect_recipes_for_keyword, periodic_collection

# データ収集の間隔（時間）
COLLECT_INTERVAL_HOURS = int(os.getenv("COLLECT_INTERVAL_HOURS", "24"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """サーバ起動時にバックグラウンドでデータ収集を開始"""
    task = asyncio.create_task(
        periodic_collection(
            interval_hours=COLLECT_INTERVAL_HOURS,
            fetch_category_list=fetch_category_list,
            search_categories=search_categories,
            fetch_category_ranking=fetch_category_ranking,
            summarize_with_gemini=summarize_with_gemini,
        )
    )
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

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
lib = ctypes.CDLL('./libGA.dll')
TagListType = (ctypes.c_char * 64) * 100
lib.ga_main.argtypes = [
    ctypes.POINTER(DataPoint), # DataItem* dataset
    ctypes.c_int,             # int n
]

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
        tip_left = 0
        tip_top = 0
        tip_rotate = (random.random() - 0.5) * 10
        
        display_tips.append(TipDisplay(
            id=item["id"],
            tipTitle=item["tipTitle"],
            tipExplanation=item["tipExplanation"],
            tipTop=tip_top,
            tipLeft=tip_left,
            tipRotate=tip_rotate,
            subTags=item.get("subTags", []),
            source=item["source"],
            tipLikes=item["tipLikes"],
            tipDislikes=item["tipDislikes"],
            upLoadDate=item["upLoadDate"]
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


# ===================================================================
# データ収集機能（楽天レシピAPI → Gemini → dbAll.json）
# ===================================================================

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")

CATEGORY_LIST_URL = "https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryList/20170426"
CATEGORY_RANKING_URL = "https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryRanking/20170426"


async def fetch_category_list() -> dict:
    """カテゴリ一覧を取得"""
    params = {
        "format": "json",
        "applicationId": RAKUTEN_APP_ID,
        "accessKey": RAKUTEN_ACCESS_KEY,
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(CATEGORY_LIST_URL, params=params)
    if res.status_code != 200:
        raise Exception(f"カテゴリ一覧の取得に失敗: {res.status_code}")
    return res.json()


def search_categories(category_data: dict, keyword: str) -> list[dict]:
    """キーワードに一致するカテゴリを検索"""
    matched = []
    result = category_data.get("result", {})
    for cat in result.get("large", []):
        if keyword in cat["categoryName"]:
            matched.append({"categoryId": str(cat["categoryId"]), "categoryName": cat["categoryName"]})
    for cat in result.get("medium", []):
        if keyword in cat["categoryName"]:
            matched.append({"categoryId": f"{cat['parentCategoryId']}-{cat['categoryId']}", "categoryName": cat["categoryName"]})
    for cat in result.get("small", []):
        if keyword in cat["categoryName"]:
            matched.append({"categoryId": f"{cat['parentCategoryId']}-{cat['categoryId']}", "categoryName": cat["categoryName"]})
    return matched


async def fetch_category_ranking(category_id: str) -> dict:
    """カテゴリIDからランキングレシピを取得"""
    params = {
        "format": "json",
        "applicationId": RAKUTEN_APP_ID,
        "accessKey": RAKUTEN_ACCESS_KEY,
        "categoryId": category_id,
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(CATEGORY_RANKING_URL, params=params)
    if res.status_code != 200:
        raise Exception(f"ランキング取得失敗: {res.status_code}")
    return res.json()


def fallback_transform(recipes: list[dict]) -> list[dict]:
    """Gemini APIが使えない場合のフォールバック変換"""
    tips = []
    for i, recipe in enumerate(recipes):
        publish = recipe.get("recipePublishday", "")
        date_str = publish.split(" ")[0] if publish else ""
        tips.append({
            "tipTitle": recipe.get("recipeTitle", ""),
            "tipExplanation": recipe.get("recipeDescription", ""),
            "mainTags": recipe.get("recipeMaterial", [])[:3],
            "subTags": [recipe.get("categoryName", "")],
            "source": [recipe.get("recipeUrl", "")],
            "upLoadDate": date_str,
        })
    return tips


async def summarize_with_gemini(recipes: list[dict]) -> list[dict]:
    """Gemini APIを使ってレシピデータをTips形式に要約"""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY 未設定 → フォールバック変換を使用")
        return fallback_transform(recipes)

    recipes_for_prompt = [
        {k: r.get(k, "") for k in ("recipeTitle", "recipeDescription", "recipeMaterial", "categoryName")}
        for r in recipes
    ]

    prompt = (
        "以下の楽天レシピのデータを、料理Tipsカードとして表示するために加工してください。\n"
        "料理の材料毎に、材料の調理のコツや方法について以下のJSON形式で出力してください。\n"
        "JSONの配列のみを出力してください。\n"
        "出力形式:\n"
        '[\n  {\n    "tipTitle": "短く簡潔なタイトル",\n'
        '    "tipExplanation": "簡潔な料理のコツ（40文字以内）",\n'
        '    "mainTags": ["素材や種類1つ"],\n'
        '    "subTags": ["調理方法を最大3つ"]\n  }\n]\n\n'
        "レシピデータ:\n"
        f"{json.dumps(recipes_for_prompt, ensure_ascii=False)}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(GEMINI_API_URL, params={"key": GEMINI_API_KEY}, json=payload)
        if res.status_code != 200:
            print(f"Gemini APIエラー: {res.status_code} {res.text}")
            return fallback_transform(recipes)
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        summaries = json.loads(text)
    except Exception as e:
        print(f"Gemini API失敗: {e}")
        return fallback_transform(recipes)

    tips = []
    for i, recipe in enumerate(recipes):
        summary = summaries[i] if i < len(summaries) else {}
        publish = recipe.get("recipePublishday", "")
        date_str = publish.split(" ")[0] if publish else ""
        tips.append({
            "tipTitle": summary.get("tipTitle", recipe.get("recipeTitle", "")),
            "tipExplanation": summary.get("tipExplanation", recipe.get("recipeDescription", "")),
            "mainTags": summary.get("mainTags", recipe.get("recipeMaterial", [])[:3]),
            "subTags": summary.get("subTags", [recipe.get("categoryName", "")]),
            "source": [recipe.get("recipeUrl", "")],
            "upLoadDate": date_str,
        })
    return tips


# --- データ収集エンドポイント ---

@app.post("/api/collect")
async def trigger_collection():
    print("[API] データ収集トリガー")
    """全キーワードでデータ収集を手動実行"""
    if not RAKUTEN_APP_ID or not RAKUTEN_ACCESS_KEY:
        raise HTTPException(status_code=500, detail="楽天APIキーが未設定です")
    total = await collect_all_recipes(
        fetch_category_list, search_categories,
        fetch_category_ranking, summarize_with_gemini,
    )
    return {"message": f"データ収集完了: {total}件保存"}


@app.post("/api/collect/{keyword}")
async def trigger_collection_keyword(keyword: str):
    print(f"[API] データ収集トリガー: {keyword}")
    """特定キーワードでデータ収集を手動実行"""
    if not RAKUTEN_APP_ID or not RAKUTEN_ACCESS_KEY:
        raise HTTPException(status_code=500, detail="楽天APIキーが未設定です")
    count = await collect_recipes_for_keyword(
        keyword,
        fetch_category_list, search_categories,
        fetch_category_ranking, summarize_with_gemini,
    )
    return {"message": f"'{keyword}' → {count}件保存"}