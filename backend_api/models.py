from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MoodHistory(Base):
    __tablename__ = "mood_history"
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_symbol_date'),
    )

    id         = Column(Integer, primary_key=True, autoincrement=True)
    symbol     = Column(String, index=True, nullable=False)
    date       = Column(Date,   index=True, nullable=False)
    mood_score = Column(Float,  nullable=False)
