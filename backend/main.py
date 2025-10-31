# backend/main.py

import os
import json
from datetime import datetime
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Core sentiment logic
from backend_api.generate_top_movers import compute_top_movers
from backend_api.scoring               import score_all_messages

# Twitter connector - COMMENTED OUT
# from backend.twitter_client            import fetch_tweets_for

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
    try:
        symbols = {}
        
        # Add top positive if it exists
        if raw.get("top_positive") and "symbol" in raw["top_positive"]:
            symbols[raw["top_positive"]["symbol"]] = raw["top_positive"]["mood_score"]
        
        # Add top negative if it exists
        if raw.get("top_negative") and "symbol" in raw["top_negative"]:
            symbols[raw["top_negative"]["symbol"]] = raw["top_negative"]["mood_score"]
        
        # Add rest positive symbols
        for s in raw.get("rest_positive", []):
            if "symbol" in s:
                symbols[s["symbol"]] = s["mood_score"]
        
        # Add rest negative symbols
        for s in raw.get("rest_negative", []):
            if "symbol" in s:
                symbols[s["symbol"]] = s["mood_score"]
        
        entry = {
            "date": datetime.utcnow().date().isoformat(),
            "market_mood":       raw["market_mood"],
            "market_confidence": raw["market_confidence"],
            "symbols": symbols
        }
        
        history = json.load(open(HISTORY_FILE)) if os.path.exists(HISTORY_FILE) else []
        history.append(entry)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        print("✅ Logged sentiment history")
    except Exception as e:
        print(f"❌ ERROR in log_sentiment_history: {e}")
        import traceback
        traceback.print_exc()
        raise e

@app.get("/top-movers")
def get_top_movers():
    """
    1) Compute core sentiment
    2) Fetch & score Twitter - COMMENTED OUT
    3) Log + return combined payload
    """
    try:
        print("🔍 DEBUG: Starting get_top_movers")
        data = compute_top_movers()
        print("🔍 DEBUG: Got data from compute_top_movers")

        # Twitter sentiment - COMMENTED OUT
        # try:
        #     symbols = (
        #         data["top_positive"]["symbol"],
        #         data["top_negative"]["symbol"],
        #     )
        #     tweets = fetch_tweets_for(symbols)
        #     data["twitter_sentiment"] = score_all_messages(
        #         [{"text": t} for t in tweets]
        #     )
        # except Exception as tw_err:
        #     data["twitter_error"] = str(tw_err)

        print("🔍 DEBUG: About to log sentiment history")
        log_sentiment_history(data)
        print("🔍 DEBUG: About to return data")
        return data

    except Exception as e:
        print(f"❌ ERROR in get_top_movers: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error computing top movers: {e}")

@app.get("/history/market")
def history_market(days: int):
    history = json.load(open(HISTORY_FILE))
    slice_ = history[-days:] if days <= len(history) else history
    return [{"date": e["date"], "mood_score": e["market_mood"]} for e in slice_]

@app.get("/history/{symbol}")
def history_symbol(symbol: str, days: int):
    history = json.load(open(HISTORY_FILE))
    pts = [
        {"date": e["date"], "mood_score": e["symbols"][symbol]}
        for e in history if symbol in e["symbols"]
    ]
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