import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# 環境変数からデータベースのURLを取得（設定されていない場合はローカル用の仮URL）
# 書式: postgresql://ユーザー名:パスワード@ホスト名:ポート番号/データベース名
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# データベースエンジンの作成
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# データベースセッションの作成（これを使ってデータの追加や取得を行います）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデル（テーブル設計図）のベースクラス
Base = declarative_base()

# DBセッションを取得するための依存性注入（Dependency）関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()