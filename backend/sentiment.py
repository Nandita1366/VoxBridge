from textblob import TextBlob

# ─────────────────────────────────────────────────────────────────────────────
#  NEGATIVE SIGNAL PHRASES
#  Covers: confusion, frustration, anger — across all four supported languages.
#  Keep phrases lowercase; matching is done on lowercased input.
# ─────────────────────────────────────────────────────────────────────────────

# Confusion / can't-hear phrases
_CONFUSION_PHRASES = [
    # English
    "i don't understand", "didn't understand", "please repeat",
    "say that again", "what did you say", "i can't hear",
    # Hindi
    "nahi samjha", "samajh nahi", "kya bol rahe", "dobara bolo",
    "sunai nahi diya", "phir se batao",
    # Kannada
    "artha aagilla", "gottagilla", "matte heli", "keli gottilla",
    # Marathi
    "mala samajle nahi", "punha sanga", "aikale nahi",
]

# Frustration / anger phrases
_ANGER_PHRASES = [
    # English
    "this is wrong", "not working", "ridiculous", "unacceptable",
    "waste of time", "terrible", "awful", "horrible", "useless",
    "call back", "speak to someone", "real person", "human agent",
    # Hindi
    "bahut bura", "galat hai", "bekar hai", "bakwaas", "kaam nahi kar raha",
    "gussa", "frustrate", "pagal", "bewakoof",
    # Kannada
    "thumba kashtav", "beda", "sariyilla", "bekar",
    # Marathi
    "chukiche aahe", "nako", "bekar aahe", "raga aala",
]

_ALL_NEG_PHRASES = _CONFUSION_PHRASES + _ANGER_PHRASES

# ─────────────────────────────────────────────────────────────────────────────
#  POSITIVE SIGNAL PHRASES  (used to dampen streak reset — see below)
# ─────────────────────────────────────────────────────────────────────────────
_STRONG_POSITIVE_PHRASES = [
    "thank you", "thanks", "perfect", "great", "yes please", "confirmed",
    "dhanyavaad", "shukriya", "bilkul", "theek hai",
    "dhanyavadagalu", "sari",
    "dhanyawad", "barobar",
]


def analyze_sentiment(text: str) -> dict:
    """
    Returns a sentiment dict: {label, polarity, frustration_detected, anger_detected}.

    Detection strategy:
      • TextBlob polarity  — reliable only for English; used as a soft signal
      • Phrase matching    — covers all four languages; used as the hard signal

    TextBlob returning 0.0 for Hindi/Kannada/Marathi is expected; phrase
    matching carries the load for non-English input.
    """
    blob = TextBlob(text)
    polarity: float = blob.sentiment.polarity   # -1.0 → 1.0; 0.0 for non-English

    text_lower = text.lower()

    confusion_hit = any(p in text_lower for p in _CONFUSION_PHRASES)
    anger_hit     = any(p in text_lower for p in _ANGER_PHRASES)
    strong_pos    = any(p in text_lower for p in _STRONG_POSITIVE_PHRASES)

    # Label hierarchy: anger > confusion > polarity > neutral
    if anger_hit or polarity < -0.4:
        label = "NEGATIVE"
    elif confusion_hit or polarity < -0.15:
        label = "NEGATIVE"
    elif strong_pos or polarity > 0.2:
        label = "POSITIVE"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "polarity": round(polarity, 3),
        "frustration_detected": confusion_hit,
        "anger_detected": anger_hit,
    }


def update_session_sentiment(session: dict, sentiment: dict) -> dict:
    """
    Update the running negative streak for the call session.

    Streak behaviour (deliberate design choices):
      • Any NEGATIVE turn       → streak += 1
      • NEUTRAL turn            → no change  (neither reward nor punish)
      • POSITIVE turn           → streak -= 1, floor 0
        (a single "okay" no longer wipes out two frustrated turns)

    Thresholds:
      neg_streak >= 2  → should_slow_down  (SENTINEL mode in NLP)
      neg_streak >= 3  → should_escalate   (hand off to human agent)
    """
    label = sentiment["label"]

    if label == "NEGATIVE":
        session["neg_streak"] = session.get("neg_streak", 0) + 1
    elif label == "POSITIVE":
        # Decay by 1, but don't go below 0
        session["neg_streak"] = max(0, session.get("neg_streak", 0) - 1)
    # NEUTRAL → leave streak unchanged

    streak = session["neg_streak"]
    session["should_escalate"]  = streak >= 3
    session["should_slow_down"] = streak >= 2

    return session