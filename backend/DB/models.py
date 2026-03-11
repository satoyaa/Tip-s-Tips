from pathlib import Path

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# DBファイルはbackend/DB/tips.dbに配置
DB_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{DB_DIR / 'tips.db'}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Tips ↔ Tags の多対多リレーション
tip_tags = Table(
    "tip_tags",
    Base.metadata,
    Column("tip_id", Integer, ForeignKey("tips.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class TipModel(Base):
    __tablename__ = "tips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tip_title = Column(String, nullable=False)
    tip_explanation = Column(Text, nullable=False)
    source = Column(Text)  # JSON文字列として格納
    tip_likes = Column(Integer, default=0)
    tip_dislikes = Column(Integer, default=0)
    upload_date = Column(String)
    tags = relationship("TagModel", secondary=tip_tags, back_populates="tips")


class TagModel(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    tag_type = Column(String, nullable=False)  # 'main' or 'sub'
    tips = relationship("TipModel", secondary=tip_tags, back_populates="tags")


# テーブル作成
Base.metadata.create_all(engine)
