# backend_api/app.py

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import tweepy
import yfinance as yf
from textblob import TextBlob
import os, json

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from backend_api.database import SessionLocal, init_db
from backend_api.models   import MoodHistory
import backend_api.generate_mock_data_large as generate_mock_data_large

app = FastAPI()
init_db()  # create tables if they don't exist

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

USE_MOCK    = os.getenv("USE_MOCK", "false").lower() == "true"
BEARER_TOKEN= os.getenv("TWITTER_BEARER_TOKEN", "YOUR_TOKEN_HERE")
client      = tweepy.Client(bearer_token=BEARER_TOKEN)


@app.get("/sentiment/{keyword}")
def get_sentiment(keyword: str):
    if USE_MOCK:
        with open("mock/sentiment_tsla.json") as f:
            return json.load(f)
    try:
        tweets = client.search_recent_tweets(
            query=keyword, max_results=20, tweet_fields=["text"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    results = []
    if tweets and tweets.data:
        for tweet in tweets.data:
            score = TextBlob(tweet.text).sentiment.polarity
            label = "Positive" if score>0 else "Negative" if score<0 else "Neutral"
            results.append({"text": tweet.text, "score": score, "label": label})
    return results


@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    if USE_MOCK:
        with open("mock/stock_tsla.json") as f:
            return json.load(f)
    try:
        stock = yf.Ticker(symbol)
        price = stock.info.get("regularMarketPrice")
        if price is None:
            raise ValueError("Price not found.")
        return {"price": round(price, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock error: {str(e)}")


@app.get("/top-movers")
def get_top_movers():
    generate_mock_data_large.main()
    try:
        with open("mock/top_movers_large.json") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Mock data not found.")


#  ▶ Market‐level history BEFORE the symbol route
@app.get("/history/market")
def get_market_history(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Return last `days` of aggregated market mood (daily average).
    """
    cutoff = date.today() - timedelta(days=days-1)
    rows = (
        db.query(
            MoodHistory.date,
            func.avg(MoodHistory.mood_score).label("mood_score")
        )
        .filter(MoodHistory.date >= cutoff)
        .group_by(MoodHistory.date)
        .order_by(MoodHistory.date)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No market history available")
    return [
        {"date": rec.date.isoformat(), "mood_score": round(rec.mood_score, 2)}
        for rec in rows
    ]


#  ▶ Symbol‐specific history
@app.get("/history/{symbol}")
def get_history(
    symbol: str,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Return last `days` of mood_score for one symbol.
    """
    cutoff = date.today() - timedelta(days=days-1)
    rows = (
        db.query(MoodHistory)
          .filter(MoodHistory.symbol == symbol.upper())
          .filter(MoodHistory.date   >= cutoff)
          .order_by(MoodHistory.date)
          .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No history for symbol {symbol}")
    return [
        {"date": r.date.isoformat(), "mood_score": r.mood_score}
        for r in rows
    ]
