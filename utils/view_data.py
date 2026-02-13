import sqlite3
import argparse
from datetime import datetime
from tabulate import tabulate


DB_PATH = "markets.db"


def connect():
    return sqlite3.connect(DB_PATH)


def get_latest_per_market(conn, limit:int=20):
    query = """
    WITH ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY source, market_id
                   ORDER BY timestamp DESC
               ) as rn
        FROM market_snapshots
    )
    SELECT source, market_id, title, outcome,
           price, volume, timestamp
    FROM ranked
    WHERE rn = 1
    ORDER BY timestamp DESC
    LIMIT ?
    """
    return conn.execute(query, (limit,)).fetchall()


def get_recent_timeseries(conn, market_id:int, source:int, limit:int=20):
    query = """
    SELECT timestamp, price, volume
    FROM market_snapshots
    WHERE market_id = ?
    AND source = ?
    ORDER BY timestamp DESC
    LIMIT ?
    """
    return conn.execute(query, (market_id, source, limit)).fetchall()


def get_top_spreads(conn, threshold:float =0.03, limit:int =20):
    query = """
    WITH latest AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY source, market_id
                   ORDER BY timestamp DESC
               ) as rn
        FROM market_snapshots
    )
    SELECT
        k.title,
        k.market_id as kalshi_id,
        p.market_id as poly_id,
        k.price as kalshi_price,
        p.price as poly_price,
        ABS(k.price - p.price) as spread
    FROM latest k
    JOIN latest p
        ON k.title = p.title
    WHERE k.source = 'kalshi'
      AND p.source = 'polymarket'
      AND k.rn = 1
      AND p.rn = 1
      AND ABS(k.price - p.price) > ?
    ORDER BY spread DESC
    LIMIT ?
    """
    return conn.execute(query, (threshold, limit)).fetchall()


def print_table(data, headers:list[str])->None:
    """print data

    Args:
        datac: data
        headers (list[str]): headers
    """
    print(tabulate(data, headers=headers, tablefmt="pretty"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", action="store_true",
                        help="Show latest market data")
    parser.add_argument("--timeseries", type=str,
                        help="Market ID to show time-series for")
    parser.add_argument("--source", type=str,
                        help="Source for timeseries (kalshi/polymarket)")
    parser.add_argument("--spreads", action="store_true",
                        help="Show arbitrage spreads")
    args = parser.parse_args()

    conn = connect()

    if args.latest:
        data = get_latest_per_market(conn)
        print("\nLATEST SNAPSHOTS\n")
        print_table(
            data,
            ["Source", "Market ID", "Title", "Outcome",
             "Price", "Volume", "Timestamp"]
        )

    elif args.timeseries:
        if not args.source:
            print("You must provide --source for timeseries")
            return
        data = get_recent_timeseries(conn, args.timeseries, args.source)
        print(f"\nRECENT TIME-SERIES ({args.source})\n")
        print_table(
            data,
            ["Timestamp", "Price", "Volume"]
        )

    elif args.spreads:
        data = get_top_spreads(conn)
        print("\nTOP SPREAD OPPORTUNITIES\n")
        print_table(
            data,
            ["Title", "Kalshi ID", "Poly ID",
             "Kalshi Price", "Poly Price", "Spread"]
        )

    else:
        print("""
Usage:
  python view_data.py --latest
  python view_data.py --timeseries <market_id> --source kalshi
  python view_data.py --spreads
        """)


if __name__ == "__main__":
    main()
