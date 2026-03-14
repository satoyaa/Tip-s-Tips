from typing import List
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from database import Base

class TipsDatabase(Base):
    __tablename__ = "tips_database"

    # カラムの定義
    id = Column(String, primary_key=True)
    tipTitle = Column(String, nullable=False)
    tipExplanation = Column(String, nullable=False)
    mainTags = Column(JSON, nullable=False, default=[])
    subTags = Column(JSON, nullable=False, default=[])
    source = Column(JSON, nullable=False, default=[])
    tipLikes = Column(Integer, default=0)
    tipDislikes = Column(Integer, default=0)
    upLoadDate = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())