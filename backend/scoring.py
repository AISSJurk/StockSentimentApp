# scoring.py

def score_message(text: str) -> dict:
    text_lower = text.lower()

    positive_keywords = [
        "breakthrough", "record", "beat", "exceeds", "strong", "growth", "soars", "surge",
        "expands", "innovation", "upgraded", "partnership", "investment", "success", "acquisition",
        "approval", "launch", "hiring", "profit", "positive"
    ]
    negative_keywords = [
        "slump", "drop", "misses", "disappoint", "lawsuit", "antitrust", "recall", "layoffs",
        "cut", "downgrade", "problem", "delay", "regulation", "loss", "negative", "fine"
    ]

    score = 0
    for word in positive_keywords:
        if word in text_lower:
            score += 0.2
    for word in negative_keywords:
        if word in text_lower:
            score -= 0.2

    # Clamp score between -1 and 1
    score = max(min(score, 1), -1)

    if score > 0.2:
        label = "Positive"
    elif score < -0.2:
        label = "Negative"
    else:
        label = "Neutral"

    return {"text": text, "score": round(score, 2), "label": label}


def score_all_messages(messages: list) -> list:
    return [score_message(msg["text"]) for msg in messages]
