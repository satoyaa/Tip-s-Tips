import json
from pathlib import Path

JSON_PATH = Path(__file__).resolve().parent / "test.json"


def _load_json() -> list[dict]:
    """test.json を読み込む。ファイルがなければ空リストを返す。"""
    if not JSON_PATH.exists():
        return []
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(data: list[dict]):
    """test.json に書き込む。"""
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_id(existing: list[dict]) -> int:
    """既存データの最大 id + 1 を返す。"""
    if not existing:
        return 0
    return max(int(tip["id"]) for tip in existing) + 1


def save_tips_to_json(tips: list[dict]):
    """Geminiで整形済みのTipsを test.json に追記保存する。"""
    existing = _load_json()
    next_id = _next_id(existing)

    for tip_data in tips:
        existing.append({
            "id": str(next_id),
            "tipTitle": tip_data.get("tipTitle", ""),
            "tipExplanation": tip_data.get("tipExplanation", ""),
            "mainTags": tip_data.get("mainTags", []),
            "subTags": tip_data.get("subTags", []),
            "source": tip_data.get("source", []),
            "tipLikes": tip_data.get("tipLikes", 0),
            "tipDislikes": tip_data.get("tipDislikes", 0),
            "upLoadDate": tip_data.get("upLoadDate", ""),
        })
        next_id += 1

    _save_json(existing)
    print(f"[JSON] 保存完了: {len(tips)}件のTips → {JSON_PATH.name}")


def search_tips_by_keyword(keyword: str) -> list[dict]:
    """キーワードで mainTags / subTags を検索し、一致するTipsを返す。"""
    all_tips = _load_json()
    results = []
    for tip in all_tips:
        tags = tip.get("mainTags", []) + tip.get("subTags", [])
        if any(keyword in tag for tag in tags):
            results.append(tip)
    return results


def get_all_tags() -> dict:
    """全タグを mainTags / subTags に分けて返す。"""
    all_tips = _load_json()
    main_tags = set()
    sub_tags = set()
    for tip in all_tips:
        main_tags.update(tip.get("mainTags", []))
        sub_tags.update(tip.get("subTags", []))
    return {
        "mainTags": sorted(main_tags),
        "subTags": sorted(sub_tags),
    }