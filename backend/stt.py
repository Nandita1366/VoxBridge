import openai
import httpx
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

WHISPER_LANG_MAP = {
    "hi": {"bcp47": "hi-IN", "name": "Hindi"},
    "kn": {"bcp47": "kn-IN", "name": "Kannada"},
    "mr": {"bcp47": "mr-IN", "name": "Marathi"},
    "en": {"bcp47": "en-IN", "name": "English"},
}


async def transcribe_audio_url(recording_url: str, twilio_sid: str, twilio_token: str) -> dict:
    """
    Downloads Twilio recording and transcribes with Whisper.
    Auto-detects language.
    """
    auth = (twilio_sid, twilio_token)
    async with httpx.AsyncClient() as client:
        resp = await client.get(recording_url + ".mp3", auth=auth, timeout=30)
        audio_bytes = resp.content

    client_oai = openai.OpenAI(api_key=OPENAI_API_KEY)
    result = client_oai.audio.transcriptions.create(
        model="whisper-1",
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


def transcribe_speech_result(speech_result: str, bcp47_hint: str = "en-IN") -> dict:
    """
    When Twilio's built-in STT is used (SpeechResult in webhook),
    wrap it in our standard format.
    """
    code = bcp47_hint.split("-")[0].lower()
    lang_info = WHISPER_LANG_MAP.get(code, WHISPER_LANG_MAP["en"])
    return {
        "text": speech_result,
        "detected_lang_code": code,
        "bcp47": bcp47_hint,
        "lang_name": lang_info["name"],
    }
