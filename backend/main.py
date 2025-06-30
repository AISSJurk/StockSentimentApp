# backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing      import List, Dict
from datetime    import datetime
import json, os


from scoring import score_all_messages

HISTORY_FILE = "sentiment_history.json"
MOCK_DIR     = "mock"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
print(">>> STARTED main.py from:", __file__)

def log_sentiment_history(raw: Dict):
    """Append today’s full market + symbol moods to history."""
    entry = {
        "date": datetime.utcnow().date().isoformat(),
        "market_mood":       raw["market_mood"],
        "market_confidence": raw["market_confidence"],
        "symbols": {
            raw["top_positive"]["symbol"]  : raw["top_positive"]["mood_score"],
            raw["top_negative"]["symbol"]  : raw["top_negative"]["mood_score"],
            **{ s["symbol"]: s["mood_score"] for s in raw.get("rest_positive", []) },
            **{ s["symbol"]: s["mood_score"] for s in raw.get("rest_negative", []) },
        }
    }
    history = json.load(open(HISTORY_FILE)) if os.path.exists(HISTORY_FILE) else []
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

@app.get("/top-movers")
def get_top_movers():
    data = json.load(open(f"{MOCK_DIR}/top_movers.json"))
    log_sentiment_history(data)
    return data

@app.get("/history/market")
def history_market(days: int):
    history = json.load(open(HISTORY_FILE))
    # clamp to available days
    slice_ = history[-days:] if days <= len(history) else history
    return [
        {"date": e["date"], "mood_score": e["market_mood"]}
        for e in slice_
    ]

@app.get("/history/{symbol}")
def history_symbol(symbol: str, days: int):
    history = json.load(open(HISTORY_FILE))
    pts = [
        {"date": e["date"], "mood_score": e["symbols"][symbol]}
        for e in history
        if symbol in e["symbols"]
    ]
    # clamp again
    return pts[-days:] if days <= len(pts) else pts
@app.get("/sentiment/{symbol}")
def get_sentiment(symbol: str):
    path = f"{MOCK_DIR}/sentiment_{symbol.upper()}.json"
    if not os.path.exists(path):
        raise HTTPException(404, f"No sentiment data for {symbol}")
    return json.load(open(path))

@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    path = f"{MOCK_DIR}/price_{symbol.upper()}.json"
    if not os.path.exists(path):
        raise HTTPException(404, f"No price data for {symbol}")
    return json.load(open(path))

@app.post("/score")
def score_batch(messages: List[Dict]):
    return score_all_messages(messages)

