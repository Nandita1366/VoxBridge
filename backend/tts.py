from google.cloud import texttospeech
import tempfile

VOICE_CONFIG = {
    "hi-IN": {
        "language_code": "hi-IN",
        "name": "hi-IN-Wavenet-D",
        "gender": texttospeech.SsmlVoiceGender.MALE,
    },
    "kn-IN": {
        "language_code": "kn-IN",
        "name": "kn-IN-Wavenet-A",
        "gender": texttospeech.SsmlVoiceGender.FEMALE,
    },
    "mr-IN": {
        "language_code": "mr-IN",
        "name": "mr-IN-Wavenet-A",
        "gender": texttospeech.SsmlVoiceGender.FEMALE,
    },
    "en-IN": {
        "language_code": "en-IN",
        "name": "en-IN-Wavenet-D",
        "gender": texttospeech.SsmlVoiceGender.MALE,
    },
}


def synthesize_to_file(text: str, bcp47: str, slow: bool = False) -> str:
    """
    Converts text to speech and saves to a temp .mp3 file.
    Returns the file path.
    """
    tts_client = texttospeech.TextToSpeechClient()
    voice_cfg = VOICE_CONFIG.get(bcp47, VOICE_CONFIG["en-IN"])

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=voice_cfg["language_code"],
        name=voice_cfg["name"],
        ssml_gender=voice_cfg["gender"],
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85 if slow else 0.95,
        pitch=0.0,
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir="./audio_cache")
    tmp.write(response.audio_content)
    tmp.close()
    return tmp.name
