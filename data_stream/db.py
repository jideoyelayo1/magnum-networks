from sqlalchemy import (
    create_engine, Column, String, Float, DateTime,
    Integer, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import config

engine = create_engine(
    f"sqlite:///{config.DB_PATH}",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class MarketSnapshot(Base):
    """
    Market Snapshoor
    """
    __tablename__:str = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, index=True)  # kalshi or polymarket
    market_id = Column(String, index=True)
    title = Column(String)
    outcome = Column(String)
    price = Column(Float)
    volume = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index(
            "idx_source_market_time",
            "source",
            "market_id",
            "timestamp"
        ),
    )


def init_db() -> None:
    """
    Initialise Database
    """
    Base.metadata.create_all(engine)
