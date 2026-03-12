"""
データ収集モジュール

楽天レシピAPI → Gemini AI要約 → DB保存 を
ユーザ検索とは独立してバックエンドから実行する。
"""

import asyncio

from operations_JSON import save_tips_to_json

# 収集対象のキーワードリスト
#COLLECT_KEYWORDS = [
#    "肉", "魚", "野菜", "パスタ", "サラダ",
#    "スープ", "丼", "麺", "鍋", "揚げ物",
#    "焼き鳥", "カレー", "パン", "卵", "豆腐",
#]

COLLECT_KEYWORDS = [
   "肉", "魚", "野菜", "麺", "鍋", 
   "焼き鳥", "カレー", "パン", "卵", 
]



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
            #save_tips_to_db(tips)
            save_tips_to_json(tips)  # ← 変更
            print(f"[データ収集] '{keyword}' → {len(tips)}件保存完了")
            return len(tips)

        return 0
    except Exception as e:
        print(f"[データ収集] '{keyword}' でエラー: {e}")
        return 0


async def collect_all_recipes(
    fetch_category_list,
    search_categories,
    fetch_category_ranking,
    summarize_with_gemini,
):
    """全キーワードについてデータ収集を実行"""
    print("[データ収集] 開始...")
    total = 0
    for keyword in COLLECT_KEYWORDS:
        count = await collect_recipes_for_keyword(
            keyword,
            fetch_category_list,
            search_categories,
            fetch_category_ranking,
            summarize_with_gemini,
        )
        total += count
        await asyncio.sleep(1)  # API負荷軽減
    print(f"[データ収集] 完了 — 合計 {total}件保存")
    return total


async def periodic_collection(
    interval_hours: int,
    fetch_category_list,
    search_categories,
    fetch_category_ranking,
    summarize_with_gemini,
):
    """定期的にデータ収集を実行するバックグラウンドタスク"""
    while True:
        await collect_all_recipes(
            fetch_category_list,
            search_categories,
            fetch_category_ranking,
            summarize_with_gemini,
        )
        await asyncio.sleep(interval_hours * 3600)
