from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from config import BASE_URL

LANG_TWILIO_MAP = {
    "hi-IN": {"twilio_lang": "hi-IN", "voice": "Polly.Aditi"},
    "kn-IN": {"twilio_lang": "hi-IN", "voice": "Polly.Aditi"},
    "mr-IN": {"twilio_lang": "hi-IN", "voice": "Polly.Aditi"},
    "en-IN": {"twilio_lang": "en-IN", "voice": "Polly.Raveena"},
}


def build_greeting_twiml(call_sid: str) -> str:
    resp = VoiceResponse()
    say = Say(
        "Hello! Namaste! Namaskara! Namaskar! "
        "Welcome to Automaton AI. Please tell us your order in any language - "
        "English, Hindi, Kannada, or Marathi.",
        voice="Polly.Raveena",
        language="en-IN",
    )
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/process/{call_sid}",
        method="POST",
        speechTimeout="auto",
        language="hi-IN",
        enhanced=True,
        timeout=10,
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
    lang_cfg = LANG_TWILIO_MAP.get(bcp47, LANG_TWILIO_MAP["en-IN"])

    if sentinel_escalate:
        resp.say(
            "I'm connecting you to our team member now. Please hold.",
            voice="Polly.Raveena",
            language="en-IN",
        )
        resp.hangup()
        return str(resp)

    if is_final:
        resp.say(tts_text, voice=lang_cfg["voice"], language=lang_cfg["twilio_lang"])
        resp.pause(length=1)
        resp.say(
            "Thank you for your order! You will receive a WhatsApp confirmation shortly. Goodbye!",
            voice="Polly.Raveena",
            language="en-IN",
        )
        resp.hangup()
        return str(resp)

    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/process/{call_sid}",
        method="POST",
        speechTimeout="auto",
        language=lang_cfg["twilio_lang"],
        enhanced=True,
        timeout=8,
    )
    gather.say(tts_text, voice=lang_cfg["voice"], language=lang_cfg["twilio_lang"])
    resp.append(gather)
    resp.redirect(f"{BASE_URL}/voice/no-input/{call_sid}")
    return str(resp)


def build_no_input_twiml(call_sid: str) -> str:
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/process/{call_sid}",
        method="POST",
        speechTimeout="auto",
        language="hi-IN",
        enhanced=True,
        timeout=10,
    )
    gather.say("Sorry, I didn't catch that. Please say your order again.", voice="Polly.Raveena")
    resp.append(gather)
    resp.hangup()
    return str(resp)
