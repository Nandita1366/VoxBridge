from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from config import BASE_URL

# ─────────────────────────────────────────────────────────────────────────────
#  LANGUAGE → TWILIO VOICE CONFIG
#
#  Polly.Aditi  = Hindi neural voice (hi-IN).
#  There are no native AWS Polly voices for kn-IN / mr-IN, so we use Aditi
#  (best available approximation) but keep the correct BCP-47 language tag so
#  Twilio's STT still listens in the right language.
#
#  Goodbye messages are localised so non-English callers hear a farewell they
#  understand.
# ─────────────────────────────────────────────────────────────────────────────
LANG_TWILIO_MAP = {
    "hi-IN": {
        "twilio_lang": "hi-IN",
        "voice": "Polly.Aditi",
        "no_input_msg": "Maafi kijiye, mujhe samajh nahi aaya. Kripya apna order dobara batayein.",
        "goodbye_msg": "Aapke order ke liye dhanyavaad! Aapko WhatsApp par confirmation milegi. Alvida!",
        "escalate_msg": "Main aapko hamare team member se connect kar raha hoon. Please hold karein.",
    },
    "kn-IN": {
        "twilio_lang": "kn-IN",
        "voice": "Polly.Aditi",   # closest available; no native Kannada Polly voice
        "no_input_msg": "Kshamissi, nange artha aagalilla. Dayavittu nimma order matte heli.",
        "goodbye_msg": "Nimma order ge dhanyavadagalu! Nimage WhatsApp confirmation baruttade. Shubhavidai!",
        "escalate_msg": "Naanu nimage namma team member annu connect maaduttiddene. Dayavittu hold maadi.",
    },
    "mr-IN": {
        "twilio_lang": "mr-IN",
        "voice": "Polly.Aditi",   # closest available; no native Marathi Polly voice
        "no_input_msg": "Maaf kara, mala samajle nahi. Krupaya aapla order puna sanga.",
        "goodbye_msg": "Aapchya orderabaddal dhanyawad! Tumhala WhatsApp var confirmation milel. Namaskar!",
        "escalate_msg": "Mi tumhala aamchya team member shi connect karto. Krupaya hold kara.",
    },
    "en-IN": {
        "twilio_lang": "en-IN",
        "voice": "Polly.Raveena",
        "no_input_msg": "Sorry, I didn't catch that. Please say your order again.",
        "goodbye_msg": "Thank you for your order! You will receive a WhatsApp confirmation shortly. Goodbye!",
        "escalate_msg": "I'm connecting you to our team member now. Please hold.",
    },
}

_DEFAULT = LANG_TWILIO_MAP["en-IN"]


def _lang_cfg(bcp47: str) -> dict:
    return LANG_TWILIO_MAP.get(bcp47, _DEFAULT)


# ─────────────────────────────────────────────────────────────────────────────

def build_greeting_twiml(call_sid: str) -> str:
    resp = VoiceResponse()
    say = Say(
        "Hello! Namaste! Namaskara! Namaskar! "
        "Welcome to Automaton AI. Please tell us your order in any language — "
        "English, Hindi, Kannada, or Marathi.",
        voice="Polly.Raveena",
        language="en-IN",
    )
    # Use hi-IN as the STT language for the greeting gather — Twilio's
    # multilingual model handles the rest once the session language is known.
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/process/{call_sid}",
        method="POST",
        speechTimeout="auto",
        language="hi-IN",
        enhanced=True,
        speechModel="phone_call",
        timeout=8,
    )
    gather.append(say)
    resp.append(gather)
    resp.redirect(f"{BASE_URL}/voice/no-input/{call_sid}")
    return str(resp)


def build_bot_reply_twiml(
    tts_text: str,
    call_sid: str,
    bcp47: str = "en-IN",
    is_final: bool = False,
    sentinel_escalate: bool = False,
) -> str:
    resp = VoiceResponse()
    cfg = _lang_cfg(bcp47)

    if sentinel_escalate:
        resp.say(cfg["escalate_msg"], voice=cfg["voice"], language=cfg["twilio_lang"])
        resp.hangup()
        return str(resp)

    if is_final:
        resp.say(tts_text, voice=cfg["voice"], language=cfg["twilio_lang"])
        resp.pause(length=1)
        resp.say(cfg["goodbye_msg"], voice=cfg["voice"], language=cfg["twilio_lang"])
        resp.hangup()
        return str(resp)

    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/process/{call_sid}",
        method="POST",
        speechTimeout="auto",
        language=cfg["twilio_lang"],
        enhanced=True,
        timeout=8,
    )
    gather.say(tts_text, voice=cfg["voice"], language=cfg["twilio_lang"])
    resp.append(gather)
    resp.redirect(f"{BASE_URL}/voice/no-input/{call_sid}")
    return str(resp)


def build_no_input_twiml(call_sid: str, bcp47: str = "en-IN") -> str:
    """
    Prompt the caller to speak again, in their own language.
    bcp47 should be the language already detected for this session.
    Falls back to English if unknown.
    """
    cfg = _lang_cfg(bcp47)
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/process/{call_sid}",
        method="POST",
        speechTimeout="auto",
        language=cfg["twilio_lang"],
        enhanced=True,
        timeout=10,
    )
    gather.say(cfg["no_input_msg"], voice=cfg["voice"], language=cfg["twilio_lang"])
    resp.append(gather)
    resp.hangup()
    return str(resp)