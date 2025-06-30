import json
import random
from datetime import date, timedelta

filename = "sentiment_history.json"
num_days = 30  # You can change this to 7, 14, etc.

symbols = ["CE", "LHX", "KEYS", "JPM", "HCA", "EBAY", "ANSS", "CTSH", "AVY", "GD", "BWA", "CVX"]

history = []

for i in range(num_days):
    day = date.today() - timedelta(days=num_days - i - 1)
    entry = {
        "date": day.isoformat(),
        "market_mood": round(random.uniform(-1, 1), 2),
        "market_confidence": round(random.uniform(0.3, 1), 2),
        "symbols": {symbol: round(random.uniform(-1, 1), 2) for symbol in symbols}
    }
    history.append(entry)

with open(filename, "w") as f:
    json.dump(history, f, indent=2)

print(f"Generated {num_days} days of test data to {filename}")
