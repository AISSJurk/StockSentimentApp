import csv
import json
import random

# 1) Headline templates
POS_TEMPLATES = [
    "{symbol} stock surges after earnings beat",
    "{symbol} shares rally on analyst upgrade",
    "{symbol} posts record quarterly revenue",
    "{symbol} sees strong buyback announcement",
    "{symbol} beats expectations with new product sales",
]

NEU_TEMPLATES = [
    "{symbol} announces upcoming product roadmap",
    "{symbol} CEO to speak at industry conference",
    "{symbol} files quarterly SEC report",
    "{symbol} unveils corporate sustainability plan",
    "{symbol} expands to new international markets",
]

NEG_TEMPLATES = [
    "{symbol} slides amid revenue miss",
    "{symbol} faces regulatory probe",
    "{symbol} issues profit warning for next quarter",
    "{symbol} stock falls after management shakeup",
    "{symbol} hit with antitrust lawsuit",
]

def main():
    # 2) Read symbols from CSV
    symbols = []
    with open("symbols.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            symbols.append(row["Symbol"].strip())

    all_headlines = []

    # 3) Generate headlines for each symbol
    for sym in symbols:
        # pick 3–5 from each sentiment bucket
        for tmpl_list in (POS_TEMPLATES, NEU_TEMPLATES, NEG_TEMPLATES):
            count = random.randint(3, 5)
            samples = random.sample(tmpl_list, k=count)
            for tmpl in samples:
                headline = tmpl.format(symbol=sym)
                all_headlines.append({
                    "symbol": sym,
                    "text": headline
                })

    # 4) Shuffle the full list so API sampling is random
    random.shuffle(all_headlines)

    # 5) Write out to JSON
    with open("mock/all_headlines.json", "w") as f:
        json.dump(all_headlines, f, indent=2)
    print(f"✅ Wrote mock/all_headlines.json with {len(all_headlines)} entries")

if __name__ == "__main__":
    main()
