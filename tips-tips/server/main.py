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

    # 4. 結果を構築
    result = {
        "keyword": keyword,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "categories": target_categories,
        "totalRecipes": len(all_recipes),
        "recipes": all_recipes,
    }

    # 5. .json ファイルとして保存
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
