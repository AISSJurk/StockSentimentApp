#!/usr/bin/env python3
import os
import sys
import datetime
import random
import argparse

# ── MAKE SURE WE CAN IMPORT backend_api ────────────────────────────────────────
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
# ───────────────────────────────────────────────────────────────────────────────

from backend_api.database import SessionLocal, init_db
from backend_api.models   import MoodHistory

def backfill(symbol: str, days: int):
    init_db()
    db = SessionLocal()
    today = datetime.date.today()
    print(f"Backfilling {days} days for {symbol} into DB at {today.isoformat()}…")

    counts = {}
    for i in range(days):
        d = today - datetime.timedelta(days=i)
        # remove any existing row for this symbol/date
        deleted = db.query(MoodHistory)\
                    .filter_by(symbol=symbol, date=d)\
                    .delete()
        # insert a new, random score
        db.add(MoodHistory(
            symbol     = symbol,
            date       = d,
            mood_score = round(random.uniform(-1, 1), 2),
        ))
        counts[d.isoformat()] = deleted

    db.commit()
    db.close()

    print("✅ Done.")
    print("Deleted existing rows per date:")
    for date, num in counts.items():
        print(f"  {date}: deleted {num}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Backfill mood_history for a symbol")
    p.add_argument("symbol", help="Ticker symbol to backfill")
    p.add_argument(
      "--days", "-n", type=int, default=30,
      help="How many days back to backfill (default 30)")
    args = p.parse_args()

    backfill(args.symbol.upper(), args.days)
