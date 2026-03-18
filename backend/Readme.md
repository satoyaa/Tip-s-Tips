# 特殊コマンド: Geminiへの再送信と内容更新
if normalized_tag == "Gemini-Retry-Response":
    print("[Gemini-Retry-Response] Geminiへの再送信を実行します")
    await rerun_gemini_on_all_tips(db)
    normalized_tag = ""

# 開発用コマンド: 検索欄に "develop show-all-data" と入力するとDB全件をコンソール出力
if normalized_tag.lower() == "develop show-all-data":
    all_data = query.all()