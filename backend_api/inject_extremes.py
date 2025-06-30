#!/usr/bin/env python3
import json

EXTREMES = [
    {"template": "{symbol} soars 100% on record guidance", "score": 1.0},
    {"template": "{symbol} crashes 100% amid scandal",     "score": -1.0},
]

def main():
    path = "mock/all_headlines.json"
    with open(path) as f:
        data = json.load(f)

    augmented = []
    for item in data:
        symbol = item["symbol"]
        augmented.append(item)
        for ex in EXTREMES:
            augmented.append({
                "symbol": symbol,
                "text":   ex["template"].format(symbol=symbol)
            })

    with open(path, "w") as f:
        json.dump(augmented, f, indent=2)
    print(f"✅ Injected extremes into {path}: total entries now {len(augmented)}")

if __name__ == "__main__":
    main()
