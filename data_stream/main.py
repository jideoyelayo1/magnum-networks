import asyncio
from db import SessionLocal, init_db, MarketSnapshot
from polymarket_client import PolymarketClient
from kalshi_client import KalshiClient
from config import config
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)

kalshi = KalshiClient()
polymarket = PolymarketClient()


def save_snapshots(data):
    session = SessionLocal()
    try:
        for d in data:
            row = MarketSnapshot(
                source=d["source"],
                market_id=d["market_id"],
                title=d["title"],
                outcome=d["outcome"],
                price=d["price"],
                volume=d["volume"],
                timestamp=datetime.now(timezone.utc)
            )
            session.add(row)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(e)
    finally:
        session.close()


async def poll():
    while True:
        try:
            kalshi_data = await kalshi.get_live_data()
            poly_data = await polymarket.get_live_data()

            all_data = kalshi_data + poly_data

            save_snapshots(all_data)

            logging.info(f"Saved {len(all_data)} snapshots")

        except Exception as e:
            logging.error(f"Polling error: {e}")

        await asyncio.sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    init_db()
    asyncio.run(poll())
