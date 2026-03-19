from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import logging
import random
import uuid
import json
import os
import ctypes
import traceback

import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import String, cast, text

import models
from database import engine, get_db, SessionLocal

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from collector import collect_all_recipes, collect_recipes_for_keyword, periodic_collection

# データ収集の間隔（時間）
COLLECT_INTERVAL_HOURS = int(os.getenv("COLLECT_INTERVAL_HOURS", "24"))

# データ収集の実行フラグ（true: API使用, false: 既存データのみ）
COLLECT_EXE = os.getenv("COLLECT_EXE", "true").lower() == "true"

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """サーバ起動時にバックグラウンドでデータ収集を開始"""
    if COLLECT_EXE:
        task = asyncio.create_task(
            periodic_collection(
                interval_hours=COLLECT_INTERVAL_HOURS,
                keywords=tag_list,
                fetch_category_list=fetch_category_list,
                search_categories=search_categories,
                fetch_category_ranking=fetch_category_ranking,
                summarize_with_gemini=summarize_with_gemini,
            )
        )
        yield
        task.cancel()
    else:
        print("[起動] COLLECT_EXE=false: データ収集をスキップし、既存データを使用します")
        yield


app = FastAPI(lifespan=lifespan)

# CORS設定（Reactからのアクセス許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tips-tips.jp"], # 本番環境ではCloudFrontのURLを指定する
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

#タグリスト（食材系）
tag_list = ["肉", "魚", "野菜", "麺", "鍋", "焼き鳥", "カレー", "パン", "卵"]
#sub_tags = ["煮る", "焼く", "蒸す", "揚げる", "生", "切る", "混ぜる", "盛り付ける"]
sub_tags = ["煮る(茹でる)", "焼く", "蒸す", "揚げる", "生", "切る", "混ぜる", "盛り付ける","味付ける","潰す","炙る","研ぐ","剥く","調理済み(レトルト)","注ぐ"] 

#lib = ctypes.CDLL('./libGA2.dll') #Windows向け
lib = ctypes.CDLL('./libGA.so') #Linux向け

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


async def rerun_gemini_on_all_tips(db: Session) -> int:
    """既存DBデータに対してGemini APIを再実行し、要約内容を更新する"""
    tips = db.query(models.TipsDatabase).all()
    if not tips:
        print("[Gemini-Retry-Response] 更新対象のデータがありません")
        return 0

    recipes = []
    ids = []
    for tip in tips:
        ids.append(tip.id)
        recipes.append({
            "recipeTitle": tip.tipTitle,
            "recipeDescription": tip.tipExplanation,
            "recipeMaterial": tip.mainTags,
            "categoryName": tip.subTags[0] if tip.subTags else "",
            # source/url は再生成しないため空にしておく
            "recipeUrl": "",
            "recipePublishday": "",
        })

    summaries = await summarize_with_gemini(recipes)

    updated = 0
    for tip_id, summary in zip(ids, summaries):
        tip = db.query(models.TipsDatabase).filter(models.TipsDatabase.id == tip_id).first()
        if not tip:
            continue
        tip.tipTitle = summary.get("tipTitle", tip.tipTitle)
        tip.tipExplanation = summary.get("tipExplanation", tip.tipExplanation)
        tip.mainTags = summary.get("mainTags", tip.mainTags)
        tip.subTags = summary.get("subTags", tip.subTags)
        updated += 1

    db.commit()
    print(f"[Gemini-Retry-Response] 更新完了: {updated}件")
    return updated


#検索表示用のデータ読み込み
@app.get("/tips", response_model=List[TipDisplay])
async def get_tips(
    tag: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    order: Optional[str] = Query("desc"),
    db: Session = Depends(get_db),
):  # クエリパラメータ 'tag' を定義
    query = db.query(models.TipsDatabase)

    normalized_tag = (tag or "").replace("\u3000", " ").strip()

    # 特殊コマンド: Geminiへの再送信と内容更新
    if normalized_tag == "Gemini-Retry-Response":
        print("[Gemini-Retry-Response] Geminiへの再送信を実行します")
        await rerun_gemini_on_all_tips(db)
        normalized_tag = ""

    # 開発用コマンド: 検索欄に "develop show-all-data" と入力するとDB全件をコンソール出力
    if normalized_tag.lower() == "develop show-all-data":
        all_data = query.all()
        payload = [
            {
                "id": item.id,
                "tipTitle": item.tipTitle,
                "tipExplanation": item.tipExplanation,
                "mainTags": item.mainTags,
                "subTags": item.subTags,
                "source": item.source,
                "tipLikes": item.tipLikes,
                "tipDislikes": item.tipDislikes,
                "upLoadDate": item.upLoadDate,
            }
            for item in all_data
        ]
        print("[develop show-all-data] DB全件出力開始")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("[develop show-all-data] DB全件出力終了")
        normalized_tag = ""

    # 1. バックエンド側でのフィルタリング
    if normalized_tag:
        # mainTags が JSON 配列なら要素を走査、そうでなければ文字列として一致確認
        # （db によっては JSON が文字列として保存される場合があるため）
        query = query.filter(
            text(
                "(" +
                "(json_typeof(\"mainTags\") = 'array' AND EXISTS (" +
                "  SELECT 1 FROM json_array_elements_text(\"mainTags\") AS t WHERE t ILIKE :p" +
                "))" +
                " OR (json_typeof(\"mainTags\") <> 'array' AND \"mainTags\"::text ILIKE :p)" +
                ")"
            ).bindparams(p=f'%{normalized_tag}%')
        )

    # 2. ソート（人気順）
    if sort == "likes":
        if order == "asc":
            query = query.order_by(models.TipsDatabase.tipLikes.asc())
        else:
            query = query.order_by(models.TipsDatabase.tipLikes.desc())

    filtered_data = query.all()

    # ソート（人気順）で取得した際の並び順をログ出力
    if sort == "likes":
        order_label = "ASC" if order == "asc" else "DESC"
        ordered = [(item.id, item.tipLikes) for item in filtered_data]
        print(f"[sort=likes order={order_label}] {ordered}")

    # 3. 絞り込み後のリストに対して表示用計算を行う
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

    if len(display_tips) <= 0:
        print("[GA] skipped: n <= 0 (no tips to arrange)")
        return display_tips

    # C側ライブラリの内部配列サイズには上限があるため、念の為上限以内に切り詰める
    # (libGA.so で MAX_TIPS 100 程度が固定されている想定)
    MAX_TIPS = 100
    if len(display_tips) > MAX_TIPS:
        print(f"[GA] trimmed display_tips from {len(display_tips)} to {MAX_TIPS} to avoid C buffer overflow")
        display_tips = display_tips[:MAX_TIPS]

    c_array, num_tips = convert_tips_to_c_array(display_tips)
    c_tag_array, num_tags = convert_tags_to_c_array(tag_list)
    lib.ga_main(c_array, num_tips, c_tag_array, num_tags)
    for i in range(num_tips):
        display_tips[i].tipLeft = c_array[i].x
        display_tips[i].tipTop = c_array[i].y
    return display_tips

#ユーザ投稿の新しいデータの追加
@app.post("/tips", response_model=Tip)
async def create_tip(tip_in: TipCreate, db: Session = Depends(get_db)):
    # 自動タグ付け（Gemini API → フォールバック）
    tags = await auto_tag_with_gemini(tip_in.tipTitle, tip_in.tipExplanation)

    # バックエンド側でデータを補間
    new_tip = models.TipsDatabase(
        id=str(uuid.uuid4())[:8],  # 重複しないIDを生成（例: "a1b2c3d4"）
        tipTitle=tip_in.tipTitle,
        tipExplanation=tip_in.tipExplanation,
        mainTags=tags["mainTags"],
        subTags=tags["subTags"],
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

    # 受信した値をログに出しておく（保存されない問題の調査用）
    logger.info(f"[likes] update request: tip_id={tip_id} tipLikes={update_data.tipLikes}")

    # データを更新（文字列でも受け入れる）
    try:
        tip.tipLikes = int(update_data.tipLikes)
    except Exception:
        tip.tipLikes = update_data.tipLikes  # そのまま入れる（整数以外でも保持される）

    db.commit()
    db.refresh(tip)

    logger.info(f"[likes] updated DB: tip_id={tip_id} tipLikes={tip.tipLikes}")

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
            logger.info(f"[batch-likes] update request: tip_id={tip_id} tipLikes={likes_count}")
            try:
                tip.tipLikes = int(likes_count)
            except Exception:
                tip.tipLikes = likes_count
            logger.info(f"[batch-likes] updated DB: tip_id={tip_id} tipLikes={tip.tipLikes}")

    db.commit()
    return {"updated": list(batch.updates.keys())}


# ===================================================================
# データ収集機能（楽天レシピAPI → Gemini → PostgreSQL）
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
    print("[楽天API] カテゴリ一覧取得完了")
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
    print(f"[楽天API] カテゴリランキング取得完了: {category_id}")
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
        f"このリストには {len(recipes)} 件のレシピがあります。必ず {len(recipes)} 件の要素を持つJSON配列（[...]）のみを出力してください。\n"
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
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post(GEMINI_API_URL, params={"key": GEMINI_API_KEY}, json=payload)
        if res.status_code != 200:
            print(f"Gemini APIエラー: {res.status_code} {res.text}")
            return fallback_transform(recipes)

        try:
            response_json = res.json()
            print(f"[Gemini API] レスポンス取得完了")
            print(f"[Gemini API] レスポンス: {json.dumps(response_json, ensure_ascii=False)}")
        except Exception as e:
            print(f"[Gemini API] レスポンスJSON変換失敗: {e} / raw: {res.text}")
            return fallback_transform(recipes)

        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        summaries = json.loads(text)

        # デバッグ: recipes[i] と summaries[i] の対応をログ出力（ずれがないか確認する）
        max_check = min(len(recipes), len(summaries))
        print(f"[Gemini対応確認] recipes={len(recipes)} summaries={len(summaries)}")
        for i in range(max_check):
            print(
                f"[Gemini対応確認] idx={i} recipeTitle={recipes[i].get('recipeTitle')!r} "
                f"=> summaryTitle={summaries[i].get('tipTitle')!r}"
            )
        if len(recipes) != len(summaries):
            print(f"[Gemini対応確認] 件数不一致: recipes={len(recipes)} summaries={len(summaries)}")

    except Exception as e:
        print(f"Gemini API失敗: {type(e).__name__} {repr(e)}")
        print(traceback.format_exc())
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


def auto_tag_fallback(title: str, explanation: str) -> dict:
    """キーワードマッチングによるフォールバックタグ付け"""
    text = title + " " + explanation
    matched_main = [t for t in tag_list if t in text]
    matched_sub = [t for t in sub_tags if t in text]
    return {"mainTags": matched_main[:2], "subTags": matched_sub[:3]}


async def auto_tag_with_gemini(title: str, explanation: str) -> dict:
    """Gemini APIを使ってユーザ投稿にタグを付与する"""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY 未設定 → キーワードマッチングを使用")
        return auto_tag_fallback(title, explanation)

    prompt = (
        "以下の料理Tipに対して、適切なタグを選択してください。\n"
        f"タイトル: {title}\n"
        f"説明: {explanation}\n\n"
        f"mainTags（食材・種類）は以下のリストから最大2つ選んでください: {tag_list}\n"
        f"subTags（調理方法）は以下のリストから最大3つ選んでください: {sub_tags}\n\n"
        "JSONのみを出力してください:\n"
        '{"mainTags": ["..."], "subTags": ["..."]}'
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(GEMINI_API_URL, params={"key": GEMINI_API_KEY}, json=payload)
        if res.status_code != 200:
            print(f"Geminiタグ付けエラー: {res.status_code} → キーワードマッチングを使用")
            return auto_tag_fallback(title, explanation)
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
        return {
            "mainTags": [t for t in result.get("mainTags", []) if t in tag_list],
            "subTags": [t for t in result.get("subTags", []) if t in sub_tags],
        }
    except Exception as e:
        print(f"Geminiタグ付け失敗: {e} → キーワードマッチングを使用")
        return auto_tag_fallback(title, explanation)


# --- データ収集エンドポイント ---

@app.post("/api/collect")
async def trigger_collection():
    """全キーワードでデータ収集を手動実行"""
    print("[API] データ収集トリガー")
    if not COLLECT_EXE:
        raise HTTPException(status_code=400, detail="COLLECT_EXE=falseのため、データ収集は無効です")
    if not RAKUTEN_APP_ID or not RAKUTEN_ACCESS_KEY:
        raise HTTPException(status_code=500, detail="楽天APIキーが未設定です")
    total = await collect_all_recipes(
        tag_list,
        fetch_category_list, search_categories,
        fetch_category_ranking, summarize_with_gemini,
    )
    return {"message": f"データ収集完了: {total}件保存"}


@app.post("/api/collect/{keyword}")
async def trigger_collection_keyword(keyword: str):
    """特定キーワードでデータ収集を手動実行"""
    print(f"[API] データ収集トリガー: {keyword}")
    if not COLLECT_EXE:
        raise HTTPException(status_code=400, detail="COLLECT_EXE=falseのため、データ収集は無効です")
    if not RAKUTEN_APP_ID or not RAKUTEN_ACCESS_KEY:
        raise HTTPException(status_code=500, detail="楽天APIキーが未設定です")
    count = await collect_recipes_for_keyword(
        keyword,
        fetch_category_list, search_categories,
        fetch_category_ranking, summarize_with_gemini,
    )
    return {"message": f"'{keyword}' → {count}件保存"}
