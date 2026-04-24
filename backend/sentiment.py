from textblob import TextBlob

LANG_NEG_PHRASES = [
    "nahi samjha",
    "samajh nahi",
    "kya bol rahe",
    "dobara bolo",
    "i don't understand",
    "please repeat",
    "what did you say",
    "artha aagilla",
    "gottagilla",
    "mala samajle nahi",
    "punha sanga",
]


def analyze_sentiment(text: str) -> dict:
    """
    Returns sentiment label and score.
    Uses TextBlob for English + keyword matching for Indian languages.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1

    text_lower = text.lower()
    frustration_detected = any(phrase in text_lower for phrase in LANG_NEG_PHRASES)

    if frustration_detected or polarity < -0.3:
        label = "NEGATIVE"
    elif polarity > 0.2:
        label = "POSITIVE"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "polarity": round(polarity, 3),
        "frustration_detected": frustration_detected,
    }


def update_session_sentiment(session: dict, sentiment: dict) -> dict:
    """Update the running negative streak for a session."""
    if sentiment["label"] == "NEGATIVE" or sentiment["frustration_detected"]:
        session["neg_streak"] = session.get("neg_streak", 0) + 1
    else:
        session["neg_streak"] = 0

    session["should_escalate"] = session["neg_streak"] >= 3
    session["should_slow_down"] = session["neg_streak"] >= 2
    return session
