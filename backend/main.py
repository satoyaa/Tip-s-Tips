import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

import os

APP_ID = os.getenv("RAKUTEN_APP_ID")
ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")

CATEGORY_LIST_URL = "https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryList/20170426"
CATEGORY_RANKING_URL = "https://openapi.rakuten.co.jp/recipems/api/Recipe/CategoryRanking/20170426"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

app = FastAPI()


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
        "各レシピについて以下のJSON形式で出力してください。\n"
        "JSONの配列のみを出力してください。\n\n"
        "出力形式:\n"
        "[\n"
        "  {\n"
        '    "tipTitle": "短く魅力的なタイトル（15文字以内）",\n'
        '    "tipExplanation": "簡潔でわかりやすい料理のコツや説明（40文字以内、文が途中で切れないようにすること）",\n'
        '    "mainTags": ["メイン食材を材料から最大3つ"],\n'
        '    "subTags": ["調理法や特徴を最大2つ"]\n'
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


@app.post("/api/search")
async def search_recipes(body: SearchRequest):
    keyword = body.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="キーワードを入力してください")

    if not APP_ID or not ACCESS_KEY:
        raise HTTPException(
            status_code=500,
            detail="RAKUTEN_APP_ID または RAKUTEN_ACCESS_KEY が設定されていません。.env ファイルを確認してください。",
        )

    # 1. カテゴリ一覧取得
    category_data = await fetch_category_list()

    # 2. キーワードでカテゴリ検索
    matched_categories = search_categories(category_data, keyword)

    if not matched_categories:
        return {
            "keyword": keyword,
            "categories": [],
            "recipes": [],
            "message": "一致するカテゴリが見つかりませんでした",
        }

    # 3. 各カテゴリのランキングレシピを取得（最大5カテゴリ）
    target_categories = matched_categories[:5]
    all_recipes = []

    for cat in target_categories:
        try:
            ranking_data = await fetch_category_ranking(cat["categoryId"])
            for recipe in ranking_data.get("result", []):
                all_recipes.append({
                    "recipeId": recipe.get("recipeId"),
                    "recipeTitle": recipe.get("recipeTitle"),
                    "recipeDescription": recipe.get("recipeDescription"),
                    "foodImageUrl": recipe.get("foodImageUrl"),
                    "recipeMaterial": recipe.get("recipeMaterial"),
                    "recipeUrl": recipe.get("recipeUrl"),
                    "recipePublishday": recipe.get("recipePublishday"),
                    "shop": recipe.get("shop"),
                    "pickup": recipe.get("pickup"),
                    "recipeCost": recipe.get("recipeCost"),
                    "recipeIndication": recipe.get("recipeIndication"),
                    "categoryName": cat["categoryName"],
                    "categoryId": cat["categoryId"],
                })
        except Exception as e:
            print(f"カテゴリ {cat['categoryName']} のランキング取得エラー: {e}")

    # 4. Gemini APIでレシピを要約してDemoData形式に変換
    tips = await summarize_with_gemini(all_recipes)

    # 5. 結果を構築（元データも保持）
    result = {
        "keyword": keyword,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "categories": target_categories,
        "totalRecipes": len(all_recipes),
        "recipes": all_recipes,
        "tips": tips,
    }

    # 6. .json ファイルとして保存
    timestamp = int(time.time() * 1000)
    safe_keyword = re.sub(r'[<>:"/\\|?*]', "_", keyword)
    file_name = f"{safe_keyword}_{timestamp}.json"
    file_path = DATA_DIR / file_name
    file_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"保存完了: {file_path}")

    return {**result, "savedFile": file_name}


@app.get("/api/files")
async def list_files():
    files = [f.name for f in DATA_DIR.glob("*.json")]
    return {"files": files}
