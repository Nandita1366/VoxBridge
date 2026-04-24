import httpx
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

WHISPER_LANG_MAP = {
    "hi": {"bcp47": "hi-IN", "name": "Hindi"},
    "kn": {"bcp47": "kn-IN", "name": "Kannada"},
    "mr": {"bcp47": "mr-IN", "name": "Marathi"},
    "en": {"bcp47": "en-IN", "name": "English"},
}

# ─────────────────────────────────────────────────────────────────────────────
#  Script-range constants
# ─────────────────────────────────────────────────────────────────────────────
_DEVANAGARI_RANGE = ("\u0900", "\u097F")   # Hindi AND Marathi
_KANNADA_RANGE    = ("\u0C80", "\u0CFF")

# Marathi-specific Devanagari characters / common syllables that never appear
# in standard Hindi.  Presence of any → lean toward Marathi.
_MARATHI_MARKERS = {
    "\u0933",   # ळ  (La — very common in Marathi, rare in Hindi)
    "\u0DA3",   # Marathi exclusive ḷa  (edge case, keep for safety)
}
# Common Marathi function words written in Devanagari Roman transliteration
# that Twilio STT sometimes returns instead of Devanagari glyphs.
_MARATHI_ROMAN_MARKERS = {
    "aahe", "aahes", "mala", "tumhi", "karu", "nahi", "sangto",
    "punha", "krupaya", "swagat",
}
_HINDI_ROMAN_MARKERS = {
    "hai", "hain", "kya", "mujhe", "chahiye", "aapka", "aapki",
    "bataiye", "dobara", "namaskar",
}


async def transcribe_audio_url(
    recording_url: str,
    twilio_sid: str,
    twilio_token: str,
) -> dict:
    """
    Downloads a Twilio recording and transcribes it with Groq Whisper.
    Auto-detects language.

    NOTE: This function is available for future use (e.g. post-call analytics
    or a recording-webhook flow).  The live call path uses transcribe_speech_result
    because Twilio's built-in STT already returns a text SpeechResult.
    """
    auth = (twilio_sid, twilio_token)
    async with httpx.AsyncClient() as http:
        resp = await http.get(recording_url + ".mp3", auth=auth, timeout=30)
        audio_bytes = resp.content

    result = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=("audio.mp3", audio_bytes, "audio/mpeg"),
        response_format="verbose_json",
        temperature=0,
    )

    detected = result.language or "en"
    lang_info = WHISPER_LANG_MAP.get(detected, WHISPER_LANG_MAP["en"])

    return {
        "text": result.text.strip(),
        "detected_lang_code": detected,
        "bcp47": lang_info["bcp47"],
        "lang_name": lang_info["name"],
    }


def _devanagari_is_marathi(text: str) -> bool:
    """
    Heuristic to distinguish Marathi from Hindi when both use Devanagari.

    Strategy (in priority order):
      1. Marathi-exclusive Unicode character ळ present → Marathi
      2. Count Roman-transliterated marker words for each language
         (Twilio STT sometimes returns Roman even for Devanagari speech)
      3. bcp47_hint supplied by caller (checked before this function is called)
      4. Default → Hindi (more common fallback)
    """
    # 1. Hard Unicode marker
    if any(ch in _MARATHI_MARKERS for ch in text):
        return True

    # 2. Roman marker word vote
    words = set(text.lower().split())
    mr_votes = len(words & _MARATHI_ROMAN_MARKERS)
    hi_votes = len(words & _HINDI_ROMAN_MARKERS)
    if mr_votes > hi_votes:
        return True

    return False


def transcribe_speech_result(speech_result: str, bcp47_hint: str = "en-IN") -> dict:
    """
    Twilio sends SpeechResult as plain text.  Detect the language from the
    text itself so the bot can switch among en/hi/kn/mr dynamically.

    Detection order:
      1. Kannada Unicode block → kn
      2. Devanagari Unicode block → run _devanagari_is_marathi() → mr or hi
      3. Fall back to the bcp47_hint already stored in the session
      4. Final fallback → en
    """
    text = (speech_result or "").strip()

    # Derive a safe fallback lang code from the session hint
    hint_code = (bcp47_hint.split("-")[0].lower() if bcp47_hint else "en")
    if hint_code not in WHISPER_LANG_MAP:
        hint_code = "en"

    detected = hint_code  # start with session hint, may be overridden below

    if text:
        has_kannada    = any(_KANNADA_RANGE[0]    <= ch <= _KANNADA_RANGE[1]    for ch in text)
        has_devanagari = any(_DEVANAGARI_RANGE[0] <= ch <= _DEVANAGARI_RANGE[1] for ch in text)

        if has_kannada:
            detected = "kn"
        elif has_devanagari:
            detected = "mr" if _devanagari_is_marathi(text) else "hi"
        else:
            # Roman script — keep session hint; only override if we have
            # strong Roman marker evidence.
            words = set(text.lower().split())
            mr_votes = len(words & _MARATHI_ROMAN_MARKERS)
            hi_votes = len(words & _HINDI_ROMAN_MARKERS)
            if mr_votes > hi_votes:
                detected = "mr"
            elif hi_votes > mr_votes:
                detected = "hi"
            # else: keep hint_code (could be "en" or whatever was detected last turn)

    lang_info = WHISPER_LANG_MAP.get(detected, WHISPER_LANG_MAP["en"])
    return {
        "text": text,
        "detected_lang_code": detected,
        "bcp47": lang_info["bcp47"],
        "lang_name": lang_info["name"],
    }