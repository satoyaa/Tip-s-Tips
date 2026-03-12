import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

import os

#from DB import save_tips_to_db, search_tips_by_keyword, get_all_tags
from DB import save_tips_to_json, search_tips_by_keyword, get_all_tags
from DB.collector import (
    collect_all_recipes,
    collect_recipes_for_keyword,
    periodic_collection,
)

APP_ID = os.getenv("RAKUTEN_APP_ID")
ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")

CATEGORY_LIST_URL = "https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryList/20170426"
CATEGORY_RANKING_URL = "https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryRanking/20170426"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

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


class SearchRequest(BaseModel):
    keyword: str


async def fetch_category_list() -> dict:
    """カテゴリ一覧を取得"""
    params = {
        "format": "json",
        "applicationId": APP_ID,
        "accessKey": ACCESS_KEY,
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(CATEGORY_LIST_URL, params=params)
    if res.status_code != 200:
        print(f"APIレスポンス: {res.status_code} {res.text}")
        raise HTTPException(
            status_code=502,
            detail=f"カテゴリ一覧の取得に失敗: {res.status_code}",
        )
    return res.json()


def search_categories(category_data: dict, keyword: str) -> list[dict]:
    """キーワードに一致するカテゴリを検索"""
    matched = []
    result = category_data.get("result", {})

    for cat in result.get("large", []):
        if keyword in cat["categoryName"]:
            matched.append({
                "categoryId": str(cat["categoryId"]),
                "categoryName": cat["categoryName"],
                "type": "large",
            })

    for cat in result.get("medium", []):
        if keyword in cat["categoryName"]:
            matched.append({
                "categoryId": f"{cat['parentCategoryId']}-{cat['categoryId']}",
                "categoryName": cat["categoryName"],
                "type": "medium",
            })

    for cat in result.get("small", []):
        if keyword in cat["categoryName"]:
            matched.append({
                "categoryId": f"{cat['parentCategoryId']}-{cat['categoryId']}",
                "categoryName": cat["categoryName"],
                "type": "small",
            })

    return matched


async def fetch_category_ranking(category_id: str) -> dict:
    """カテゴリIDからランキングレシピを取得"""
    params = {
        "format": "json",
        "applicationId": APP_ID,
        "accessKey": ACCESS_KEY,
        "categoryId": category_id,
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(CATEGORY_RANKING_URL, params=params)
    if res.status_code != 200:
        raise Exception(f"ランキング取得失敗 (categoryId: {category_id}): {res.status_code}")
    return res.json()


def fallback_transform(recipes: list[dict]) -> list[dict]:
    """Gemini APIが使えない場合のフォールバック変換"""
    tips = []
    for i, recipe in enumerate(recipes):
        publish = recipe.get("recipePublishday", "")
        date_str = publish.split(" ")[0] if publish else ""
        tips.append({
            "id": str(recipe.get("recipeId", i)),
            "tipTitle": recipe.get("recipeTitle", ""),
            "tipExplanation": recipe.get("recipeDescription", ""),
            "mainTags": recipe.get("recipeMaterial", [])[:3],
            "subTags": [recipe.get("categoryName", "")],
            "source": [recipe.get("recipeUrl", "")],
            "upLoadDate": date_str,
        })
    return tips


async def summarize_with_gemini(recipes: list[dict]) -> list[dict]:
    """Gemini APIを使ってレシピデータをDemoData形式のTipsに要約"""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY が未設定のため、フォールバック変換を使用します")
        return fallback_transform(recipes)

    recipes_for_prompt = [
        {
            "recipeTitle": r.get("recipeTitle", ""),
            "recipeDescription": r.get("recipeDescription", ""),
            "recipeMaterial": r.get("recipeMaterial", []),
            "categoryName": r.get("categoryName", ""),
        }
        for r in recipes
    ]

    prompt = (
        "以下の楽天レシピのデータを、料理Tipsカードとして表示するために加工してください。\n"
        "料理の材料毎に、材料の調理のコツや方法について以下のJSON形式で出力してください。\n"
        "JSONの配列のみを出力してください。\n"
        "出力形式:\n"
        "[\n"
        "  {\n"
        '    "tipTitle": "短く簡潔なタイトル（感嘆符などは不要）",\n'
        '    "tipExplanation": "簡潔でわかりやすい料理のコツや説明（40文字以内、文が途中で切れないようにすること）",\n'
        '    "mainTags": ["料理の素材や種類に関する1つ"](例：「カレー」「バナナ」「鍋」等),\n'
        '    "subTags": ["調理方法や工程を最大3つ"]\n'
        "  }\n"
        "]\n\n"
        "レシピデータ:\n"
        f"{json.dumps(recipes_for_prompt, ensure_ascii=False)}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                GEMINI_API_URL,
                params={"key": GEMINI_API_KEY},
                json=payload,
            )
        if res.status_code != 200:
            print(f"Gemini APIエラー: {res.status_code} {res.text}")
            return fallback_transform(recipes)

        data = res.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        summaries = json.loads(text)
    except Exception as e:
        print(f"Gemini API呼び出し失敗: {e}")
        return fallback_transform(recipes)

    # Geminiの要約と元レシピデータを合成してDemoData形式にする
    tips = []
    for i, recipe in enumerate(recipes):
        summary = summaries[i] if i < len(summaries) else {}
        publish = recipe.get("recipePublishday", "")
        date_str = publish.split(" ")[0] if publish else ""
        tips.append({
            "id": str(recipe.get("recipeId", i)),
            "tipTitle": summary.get("tipTitle", recipe.get("recipeTitle", "")),
            "tipExplanation": summary.get("tipExplanation", recipe.get("recipeDescription", "")),
            "mainTags": summary.get("mainTags", recipe.get("recipeMaterial", [])[:3]),
            "subTags": summary.get("subTags", [recipe.get("categoryName", "")]),
            "source": [recipe.get("recipeUrl", "")],
            "upLoadDate": date_str,
        })
    return tips


# ---------------------------------------------------------------------------
# ユーザ向けAPI: DBからタグ検索のみ
# ---------------------------------------------------------------------------


@app.post("/api/search")
async def search_tips(body: SearchRequest):
    """ユーザ検索 → DBのタグから取得。ヒットなしなら明示的に通知。"""
    keyword = body.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="キーワードを入力してください")

    tips = search_tips_by_keyword(keyword)

    if not tips:
        return {
            "keyword": keyword,
            "tips": [],
            "message": "ヒットがありません",
        }

    return {
        "keyword": keyword,
        "tips": tips,
        "totalResults": len(tips),
    }


@app.get("/api/tags")
async def get_tags():
    """DBに登録されている全タグを返す"""
    return get_all_tags()


# ---------------------------------------------------------------------------
# 管理者向けAPI: 手動でデータ収集をトリガー
# ---------------------------------------------------------------------------


@app.post("/api/collect")
async def trigger_collection():
    """全キーワードについてデータ収集を手動実行"""
    if not APP_ID or not ACCESS_KEY:
        raise HTTPException(
            status_code=500,
            detail="RAKUTEN_APP_ID または RAKUTEN_ACCESS_KEY が設定されていません。",
        )
    total = await collect_all_recipes(
        fetch_category_list,
        search_categories,
        fetch_category_ranking,
        summarize_with_gemini,
    )
    return {"message": f"データ収集完了: {total}件保存"}


@app.post("/api/collect/{keyword}")
async def trigger_collection_keyword(keyword: str):
    """特定キーワードでデータ収集を手動実行"""
    if not APP_ID or not ACCESS_KEY:
        raise HTTPException(
            status_code=500,
            detail="RAKUTEN_APP_ID または RAKUTEN_ACCESS_KEY が設定されていません。",
        )
    count = await collect_recipes_for_keyword(
        keyword,
        fetch_category_list,
        search_categories,
        fetch_category_ranking,
        summarize_with_gemini,
    )
    return {"message": f"'{keyword}' のデータ収集完了: {count}件保存"}
