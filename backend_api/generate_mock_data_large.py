#!/usr/bin/env python3
import os
import json
import random
import datetime

from sqlalchemy.dialects.postgresql import insert
from backend_api.scoring import score_all_messages
from backend_api.database import SessionLocal, init_db
from backend_api.models import MoodHistory

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
MIN_PER_SYMBOL      = 5
AUTHORS             = ["Analyst", "CEO tweet", "Newswire", "Forum user", "Insider tip"]

# Sampling mix: 1 extreme + 4 normals = 20% extremes
EXTREME_COUNT       = 1
NORMAL_COUNT        = 4

# Jitter to spread the per‐symbol mood
JITTER_AMPLITUDE    = 0.1

# Credibility weights by author/source
CREDIBILITY_WEIGHTS = {
    "Analyst":     1.0,
    "CEO tweet":   1.5,
    "Newswire":    1.2,
    "Forum user":  0.7,
    "Insider tip": 0.8,
}

# Recency‐decay half‐life in hours
DECAY_HALF_LIFE_HOURS = 24.0
# ────────────────────────────────────────────────────────────────────────────────

def weight_by_source(score: float, source: str) -> float:
    return score * CREDIBILITY_WEIGHTS.get(source, 1.0)

def apply_recency_decay(score: float, timestamp: datetime.datetime, now: datetime.datetime) -> float:
    delta_hours = (now - timestamp).total_seconds() / 3600.0
    decay = 0.5 ** (delta_hours / DECAY_HALF_LIFE_HOURS)
    return score * decay

def bucket_intensity(score: float) -> str:
    if score >=  0.8: return "Strong +"
    if score >=  0.2: return "Weak +"
    if score <= -0.8: return "Strong -"
    if score <= -0.2: return "Weak -"
    return "Neutral"

def process_message(raw_score: float,
                    source: str,
                    timestamp: datetime.datetime,
                    now: datetime.datetime) -> (float, str):
    w1 = weight_by_source(raw_score, source)
    w2 = apply_recency_decay(w1, timestamp, now)
    final = max(-1.0, min(1.0, w2))
    return final, bucket_intensity(final)

def main():
    now = datetime.datetime.utcnow()

    # Resolve the project-level mock directory (one level up from this file)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    mock_dir     = os.path.join(project_root, "mock")
    headlines_fp = os.path.join(mock_dir, "all_headlines.json")
    output_fp    = os.path.join(mock_dir, "top_movers_large.json")

    # 1. Load all headlines
    with open(headlines_fp) as f:
        pool = json.load(f)

    # 2. Group by symbol
    symbol_pool = {}
    for h in pool:
        symbol_pool.setdefault(h["symbol"], []).append(h)
    symbols = list(symbol_pool)

    # 3–5. Build per‐symbol summary
    summary = []
    for sym in symbols:
        headlines = symbol_pool[sym]
        extremes  = [h for h in headlines if "100%" in h["text"]]
        normals   = [h for h in headlines if "100%" not in h["text"]]

        # Sample 1 extreme + 4 normals
        msgs = []
        if extremes:
            msgs.append(random.choice(extremes))
        if len(normals) >= NORMAL_COUNT:
            msgs.extend(random.sample(normals, k=NORMAL_COUNT))
        else:
            msgs.extend(normals)
        while len(msgs) < MIN_PER_SYMBOL:
            msgs.append(random.choice(normals or extremes))
        random.shuffle(msgs)

        # Score + weighting + decay + bucketing
        scored = []
        for m in msgs:
            text = m["text"]
            if "soars 100%" in text:
                raw_score, orig_label = 1.0, "Positive"
            elif "crashes 100%" in text:
                raw_score, orig_label = -1.0, "Negative"
            else:
                res = score_all_messages([{"text": text}])[0]
                raw_score, orig_label = res["score"], res["label"]

            author = random.choice(AUTHORS)
            if "timestamp" in m:
                try:
                    ts = datetime.datetime.fromisoformat(m["timestamp"])
                except Exception:
                    ts = now - datetime.timedelta(hours=random.uniform(0, 48))
            else:
                ts = now - datetime.timedelta(hours=random.uniform(0, 48))

            weighted_score, intensity = process_message(raw_score, author, ts, now)
            scored.append({
                "text":       text,
                "score":      round(weighted_score, 3),
                "orig_score": round(raw_score,    3),
                "label":      orig_label,
                "intensity":  intensity,
                "symbol":     sym,
                "author":     author,
                "timestamp":  ts.isoformat(),
            })

        # Compute mood & confidence
        avg = sum(m["score"] for m in scored) / len(scored)
        mood_score = round(
            max(-1, min(1, avg + random.uniform(-JITTER_AMPLITUDE, JITTER_AMPLITUDE))),
            2
        )
        pos = sum(1 for m in scored if m["score"] > 0)
        neg = sum(1 for m in scored if m["score"] < 0)
        confidence = round((pos / (pos + neg)) if (pos + neg) else 0.0, 2)

        summary.append({
            "symbol":     sym,
            "mood_score": mood_score,
            "confidence": confidence,
            "messages":   scored
        })

    # ── 6. Persist today’s score with upsert ────────────────────────────────────
    init_db()
    db = SessionLocal()
    today = now.date()

    for s in summary:
        stmt = insert(MoodHistory).values(
            symbol     = s["symbol"],
            date       = today,
            mood_score = s["mood_score"],
        ).on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_={"mood_score": insert(MoodHistory).excluded.mood_score},
        )
        db.execute(stmt)

    db.commit()
    db.close()

    # 7. Market aggregates & top movers
    scores = [s["mood_score"] for s in summary]
    confs  = [s["confidence"]   for s in summary]

    positive = sorted([s for s in summary if s["mood_score"] > 0],
                      key=lambda x: x["mood_score"], reverse=True)
    negative = sorted([s for s in summary if s["mood_score"] < 0],
                      key=lambda x: x["mood_score"])

    def make_rest(lst):
        rest = []
        for x in lst[1:6]:
            rest.append({
                "symbol":     x["symbol"],
                "mood_score": x["mood_score"],
                "confidence": x["confidence"],
                "headline":   x["messages"][0]["text"],
                "messages":   x["messages"],
            })
        return rest

    top_movers = {
        "market_mood":       round(sum(scores) / len(scores), 2),
        "market_confidence": round(sum(confs)  / len(confs),   2),
        "top_positive":      {**positive[0], "messages": positive[0]["messages"][:5]} if positive else {},
        "top_negative":      {**negative[0], "messages": negative[0]["messages"][:5]} if negative else {},
        "rest_positive":     make_rest(positive),
        "rest_negative":     make_rest(negative),
    }

    # 8. Write out JSON
    os.makedirs(mock_dir, exist_ok=True)
    with open(output_fp, "w") as f:
        json.dump(top_movers, f, indent=2)

    print(f"✅ Wrote {output_fp} (v{top_movers.get('version','?')} @ {now.isoformat()}Z)")

if __name__ == "__main__":
    main()
