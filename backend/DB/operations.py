import json

from .models import SessionLocal, TagModel, TipModel, tip_tags


def save_tips_to_db(tips: list[dict]):
    """Geminiで整形済みのTipsをDBに保存する"""
    db = SessionLocal()
    try:
        with db.no_autoflush:
            for tip_data in tips:
                tip = TipModel(
                    tip_title=tip_data["tipTitle"],
                    tip_explanation=tip_data["tipExplanation"],
                    source=json.dumps(tip_data.get("source", []), ensure_ascii=False),
                    upload_date=tip_data.get("upLoadDate", ""),
                )
                db.add(tip)
                db.flush()

                # mainTags を登録・関連付け
                for tag_name in tip_data.get("mainTags", []):
                    tag = db.query(TagModel).filter_by(name=tag_name, tag_type="main").first()
                    if not tag:
                        tag = TagModel(name=tag_name, tag_type="main")
                        db.add(tag)
                        db.flush()
                    tip.tags.append(tag)

                # subTags を登録・関連付け
                for tag_name in tip_data.get("subTags", []):
                    tag = db.query(TagModel).filter_by(name=tag_name, tag_type="sub").first()
                    if not tag:
                        tag = TagModel(name=tag_name, tag_type="sub")
                        db.add(tag)
                        db.flush()
                    tip.tags.append(tag)

        db.commit()
        print(f"[DB] 保存完了: {len(tips)}件のTips")
    except Exception as e:
        db.rollback()
        print(f"[DB] 保存エラー: {e}")
        raise
    finally:
        db.close()


def search_tips_by_keyword(keyword: str) -> list[dict]:
    """キーワードでタグを検索し、関連するTipsを返す"""
    db = SessionLocal()
    try:
        db_tips = (
            db.query(TipModel)
            .join(tip_tags)
            .join(TagModel)
            .filter(TagModel.name.contains(keyword))
            .distinct()
            .all()
        )

        tips = []
        for t in db_tips:
            tips.append({
                "id": str(t.id),
                "tipTitle": t.tip_title,
                "tipExplanation": t.tip_explanation,
                "mainTags": [tag.name for tag in t.tags if tag.tag_type == "main"],
                "subTags": [tag.name for tag in t.tags if tag.tag_type == "sub"],
                "source": json.loads(t.source) if t.source else [],
                "tipLikes": t.tip_likes,
                "tipDislikes": t.tip_dislikes,
                "upLoadDate": t.upload_date,
            })
        return tips
    finally:
        db.close()


def get_all_tags() -> dict:
    """DBに登録されている全タグを取得する"""
    db = SessionLocal()
    try:
        tags = db.query(TagModel).all()
        return {
            "mainTags": sorted(set(t.name for t in tags if t.tag_type == "main")),
            "subTags": sorted(set(t.name for t in tags if t.tag_type == "sub")),
        }
    finally:
        db.close()
