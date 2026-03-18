"""
データ収集モジュール

楽天レシピAPI → Gemini AI要約 → PostgreSQL保存 を
ユーザ検索とは独立してバックエンドから実行する。
"""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from database import SessionLocal
import models


def save_tips_to_db(tips: list[dict]):
    """Tipsデータを重複チェック付きでPostgreSQLに保存"""
    db: Session = SessionLocal()
    try:
        saved_count = 0
        for tip in tips:
            title = tip.get("tipTitle", "")

            # 重複チェック: 同じtipTitleが既に存在する場合は上書き
            existing = db.query(models.TipsDatabase).filter(
                models.TipsDatabase.tipTitle == title
            ).first()
            if existing:
                existing.tipExplanation = tip.get("tipExplanation", "")
                existing.mainTags = tip.get("mainTags", [])
                existing.subTags = tip.get("subTags", [])
                existing.source = tip.get("source", [])
                existing.upLoadDate = tip.get("upLoadDate", datetime.now().strftime("%Y/%m/%d"))
                saved_count += 1
                print(f"[データ収集] 重複上書き: {title}")
                continue

            new_tip = models.TipsDatabase(
                id=str(uuid.uuid4())[:8],
                tipTitle=title,
                tipExplanation=tip.get("tipExplanation", ""),
                mainTags=tip.get("mainTags", []),
                subTags=tip.get("subTags", []),
                source=tip.get("source", []),
                tipLikes=0,
                tipDislikes=0,
                upLoadDate=tip.get("upLoadDate", datetime.now().strftime("%Y/%m/%d")),
            )
            db.add(new_tip)
            saved_count += 1

        db.commit()
        print(f"[データ収集] {saved_count}件保存（{len(tips) - saved_count}件重複スキップ）")
        return saved_count
    except Exception as e:
        db.rollback()
        print(f"[データ収集] DB保存エラー: {e}")
        return 0
    finally:
        db.close()


async def collect_recipes_for_keyword(
    keyword: str,
    fetch_category_list,
    search_categories,
    fetch_category_ranking,
    summarize_with_gemini,
):
    """1つのキーワードについて楽天API→Gemini→DB保存を実行"""
    print(f"[データ収集] キーワード: {keyword}")
    try:
        category_data = await fetch_category_list()
        matched_categories = search_categories(category_data, keyword)

        if not matched_categories:
            print(f"[データ収集] '{keyword}' に一致するカテゴリなし")
            return 0

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
                        "recipeMaterial": recipe.get("recipeMaterial"),
                        "recipeUrl": recipe.get("recipeUrl"),
                        "recipePublishday": recipe.get("recipePublishday"),
                        "categoryName": cat["categoryName"],
                    })
            except Exception as e:
                print(f"[データ収集] {cat['categoryName']} 取得エラー: {e}")

        if all_recipes:
            tips = await summarize_with_gemini(all_recipes)
            saved = save_tips_to_db(tips)
            print(f"[データ収集] '{keyword}' → {saved}件保存完了")
            return saved

        return 0
    except Exception as e:
        print(f"[データ収集] '{keyword}' でエラー: {e}")
        return 0


async def collect_all_recipes(
    keywords,
    fetch_category_list,
    search_categories,
    fetch_category_ranking,
    summarize_with_gemini,
):
    """全キーワードについてデータ収集を実行（Geminiは1回のみ呼ぶ）"""
    print("[データ収集] 開始...")

    try:
        category_data = await fetch_category_list()
    except Exception as e:
        print(f"[データ収集] カテゴリ一覧取得失敗: {e}")
        return 0

    all_recipes = []
    for keyword in keywords:
        matched_categories = search_categories(category_data, keyword)
        if not matched_categories:
            print(f"[データ収集] '{keyword}' に一致するカテゴリなし")
            continue

        target_categories = matched_categories[:5]
        for cat in target_categories:
            try:
                ranking_data = await fetch_category_ranking(cat["categoryId"])
                for recipe in ranking_data.get("result", []):
                    all_recipes.append({
                        "recipeId": recipe.get("recipeId"),
                        "recipeTitle": recipe.get("recipeTitle"),
                        "recipeDescription": recipe.get("recipeDescription"),
                        "recipeMaterial": recipe.get("recipeMaterial"),
                        "recipeUrl": recipe.get("recipeUrl"),
                        "recipePublishday": recipe.get("recipePublishday"),
                        "categoryName": cat["categoryName"],
                        "keyword": keyword,
                    })
            except Exception as e:
                print(f"[データ収集] {keyword}/{cat['categoryName']} 取得エラー: {e}")

        await asyncio.sleep(0.5)  # API負荷軽減

    if not all_recipes:
        print("[データ収集] レシピが取得できませんでした")
        return 0

    tips = await summarize_with_gemini(all_recipes)
    saved = save_tips_to_db(tips)
    print(f"[データ収集] 完了 — 合計 {saved}件保存")
    return saved


async def periodic_collection(
    interval_hours: int,
    keywords,
    fetch_category_list,
    search_categories,
    fetch_category_ranking,
    summarize_with_gemini,
):
    """定期的にデータ収集を実行するバックグラウンドタスク"""
    while True:
        await collect_all_recipes(
            keywords,
            fetch_category_list,
            search_categories,
            fetch_category_ranking,
            summarize_with_gemini,
        )
        await asyncio.sleep(interval_hours * 3600)
