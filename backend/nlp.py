import anthropic
import json
import re
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are VoxBridge, a warm and efficient voice order assistant for Automaton AI Infosystem.

CRITICAL RULES:
1. ALWAYS respond in the EXACT same language the customer used. If they spoke Hindi, respond in Hindi. Kannada -> Kannada. Never switch languages unless asked.
2. Your replies must be SHORT - this is a PHONE CALL. Max 2-3 sentences per response.
3. Your goal: collect item_name, quantity, and delivery_address from the customer.
4. When you have all 3 fields confirmed, end your reply with this JSON on a new line:
   ORDER_CONFIRMED:{"item":"...", "qty":1, "address":"..."}
5. If the customer sounds confused, respond more simply and slowly (shorter sentences).
6. Be warm and natural, not robotic.

Language greetings reference:
- English: "Hello! Thank you for calling Automaton AI."
- Hindi: "Namaste! Automaton AI mein aapka swagat hai."
- Kannada: "Namaskara! Automaton AI ge swagatha."
- Marathi: "Namaskar! Automaton AI madhe aapale swagat aahe."

Do not say "ORDER_CONFIRMED" until you have ALL THREE fields: item, quantity, and address."""


def extract_order_from_reply(reply: str) -> dict | None:
    """Parse ORDER_CONFIRMED JSON from bot reply if present."""
    match = re.search(r"ORDER_CONFIRMED:\s*(\{.*?\})", reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None


def clean_reply_for_tts(reply: str) -> str:
    """Remove the ORDER_CONFIRMED JSON tag from spoken text."""
    return re.sub(r"ORDER_CONFIRMED:.*", "", reply).strip()


def get_bot_reply(
    customer_text: str,
    language_name: str,
    conversation_history: list,
    sentinel_mode: bool = False,
) -> dict:
    """
    Get Claude's response given conversation history.
    Returns reply text, cleaned TTS version, and order data if confirmed.
    """
    extra_hint = ""
    if sentinel_mode:
        extra_hint = "\n[SENTINEL: Customer seems confused. Use very simple, slow, short sentences.]"

    history = conversation_history.copy()
    history.append(
        {
            "role": "user",
            "content": f"[Customer spoke in {language_name}]: {customer_text}{extra_hint}",
        }
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=250,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    reply = response.content[0].text.strip()
    history.append({"role": "assistant", "content": reply})

    order_data = extract_order_from_reply(reply)
    tts_text = clean_reply_for_tts(reply)

    return {
        "full_reply": reply,
        "tts_text": tts_text,
        "order_confirmed": order_data is not None,
        "order_data": order_data,
        "updated_history": history,
    }
