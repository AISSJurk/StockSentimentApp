# generate_top_movers.py

import json
import random
from scoring import score_all_messages

print("🔍 DEBUG: Running generate_top_movers.py")

# 1. Load & score all headlines
with open("mock/all_headlines.json") as f:
    headlines = json.load(f)

scored = []
for item in headlines:
    result = score_all_messages([{"text": item["text"]}])[0]
    result["text"] = item["text"]
    result["symbol"] = item["symbol"]
    scored.append(result)

# 2. Group by symbol and compute averages
symbol_groups = {}
for item in scored:
    symbol_groups.setdefault(item["symbol"], []).append(item)

summary = []
for symbol, messages in symbol_groups.items():
    avg_score  = sum(m["score"] for m in messages) / len(messages)
    confidence = len(messages) / 5  # Rough confidence metric
    summary.append({
        "symbol":     symbol,
        "mood_score": round(avg_score, 2),
        "confidence": round(min(confidence, 1.0), 2),
        "messages":   messages
    })

print(f"🔍 DEBUG: summary contains {len(summary)} symbols")

# 3. Compute overall market metrics
all_scores        = [s["mood_score"] for s in summary]
market_mood       = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
all_confidences   = [s["confidence"] for s in summary]
market_confidence = round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else 0.0

# 4. Sort for top positive and negative
positive = sorted(
    [s for s in summary if s["mood_score"] > 0],
    key=lambda x: x["mood_score"],
    reverse=True
)
negative = sorted(
    [s for s in summary if s["mood_score"] < 0],
    key=lambda x: x["mood_score"]
)

# 5. DEMO OVERRIDE: force entries into correct sign ranges
low_conf  = random.random() * 0.4           # 0–40%
mid_conf  = 0.4 + random.random() * 0.4     # 40–80%
high_conf = 0.8 + random.random() * 0.2     # 80–100%

if positive:
    positive[0]["confidence"] = mid_conf
    # force a positive mood in [0.0, 1.0]
    positive[0]["mood_score"]  = round(random.uniform(0.0, 1.0), 2)

if negative:
    negative[0]["confidence"] = high_conf
    # force a negative mood in [-1.0, 0.0]
    negative[0]["mood_score"]  = round(random.uniform(-1.0, 0.0), 2)

# DEMO OVERRIDE for market gauge: random positive market mood [0.0,1.0]
market_confidence = low_conf
market_mood       = round(random.uniform(0.0, 1.0), 2)

# 6. Build rest_positive (next 5 positives)
rest_positive = []
for x in positive[1:6]:
    msgs = next((item["messages"] for item in summary if item["symbol"] == x["symbol"]), [])
    rest_positive.append({
        "symbol":     x["symbol"],
        "mood_score": x["mood_score"],
        "confidence": x["confidence"],
        "headline":   (msgs[0]["text"] if msgs else ""),
        "messages":   msgs
    })

# 7. Build rest_negative (next 5 negatives, with fallback)
rest_neg_list = negative[1:]
if len(rest_neg_list) < 5:
    top_neg_sym = negative[0]["symbol"] if negative else None
    others = [s for s in summary if s["symbol"] != top_neg_sym]
    others_sorted = sorted(others, key=lambda x: x["mood_score"])
    needed = 5 - len(rest_neg_list)
    for s in others_sorted:
        if s["symbol"] not in [r["symbol"] for r in rest_neg_list]:
            rest_neg_list.append(s)
            needed -= 1
            if needed == 0:
                break

rest_negative = []
for x in rest_neg_list[:5]:
    msgs = next((item["messages"] for item in summary if item["symbol"] == x["symbol"]), [])
    rest_negative.append({
        "symbol":     x["symbol"],
        "mood_score": x["mood_score"],
        "confidence": x["confidence"],
        "headline":   (msgs[0]["text"] if msgs else ""),
        "messages":   msgs
    })

# 8. Assemble top_movers payload
top_movers = {
    "market_mood":       market_mood,
    "market_confidence": market_confidence,
    "top_positive": {
        "symbol":     positive[0]["symbol"],
        "mood_score": positive[0]["mood_score"],
        "confidence": positive[0]["confidence"],
        "messages":   positive[0]["messages"][:5]
    } if positive else {},
    "top_negative": {
        "symbol":     negative[0]["symbol"],
        "mood_score": negative[0]["mood_score"],
        "confidence": negative[0]["confidence"],
        "messages":   negative[0]["messages"][:5]
    } if negative else {},
    "rest_positive": rest_positive,
    "rest_negative": rest_negative
}

# 9. Write to large mock file
with open("mock/top_movers_large.json", "w") as f:
    json.dump(top_movers, f, indent=2)
    print("✅ Wrote mock/top_movers_large.json")

