from google import genai
from google.genai import types
import json
import re
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

# ─────────────────────────────────────────────
#  PRODUCT CATALOG  —  edit this freely
# ─────────────────────────────────────────────
PRODUCT_CATALOG = """
AVAILABLE PRODUCTS (Automaton AI Infosystem):
─────────────────────────────────────────────
ELECTRONICS
  • Smart Speaker Mini       — ₹1,499   (voice-controlled, Wi-Fi)
  • Smart Speaker Pro        — ₹2,999   (premium sound, Bluetooth + Wi-Fi)
  • Wireless Earbuds X1      — ₹999     (BT 5.0, 24hr battery)
  • USB-C Hub 7-in-1         — ₹799     (HDMI, USB 3.0, SD card)
  • Desk LED Lamp (Smart)    — ₹649     (app-controlled, 3 colour modes)

OFFICE SUPPLIES
  • Ergonomic Mouse          — ₹499     (silent click, 2.4GHz)
  • Mechanical Keyboard      — ₹1,299   (TKL, brown switches)
  • Laptop Stand Aluminium   — ₹849     (adjustable, fits 11–17″)
  • Cable Management Kit     — ₹199     (velcro ties + clips, 30pc)

BUNDLES
  • Home Office Starter Pack — ₹3,299   (Mouse + Keyboard + Lamp)
  • Audio Bundle             — ₹3,799   (Smart Speaker Pro + Earbuds X1)

DELIVERY: 3–5 business days. Free delivery on orders above ₹999.
─────────────────────────────────────────────
"""

# ─────────────────────────────────────────────
#  SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are VoxBridge, a warm and efficient voice order assistant for Automaton AI Infosystem.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRODUCT KNOWLEDGE BASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{PRODUCT_CATALOG}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. LANGUAGE: Detect the customer's language from their message and ALWAYS reply in the EXACT same language.
   Supported: English, Hindi (Devanagari or Roman), Kannada, Marathi.
   Never switch languages unless the customer does first.

2. BREVITY: This is a PHONE CALL. Max 2–3 short sentences per reply. No bullet points or markdown.

3. ORDER COLLECTION GOAL:
   You must collect exactly THREE things before confirming:
     a) item_name  — match it to the catalog above
     b) quantity   — a positive integer
     c) delivery_address — full address including city/pincode

4. CATALOG GUIDANCE:
   - If the customer names a product not in the catalog, politely say it's unavailable and suggest the closest match.
   - If the customer is vague (e.g. "speaker"), ask which variant (Mini or Pro).
   - Mention the price once when the item is identified so the customer can confirm.

5. ORDER CONFIRMATION:
   Only when you have all three fields confirmed by the customer, append this JSON on a NEW LINE at the very end:
   ORDER_CONFIRMED:{{"item":"<exact product name>", "qty":<integer>, "address":"<full address>"}}
   Do NOT include ORDER_CONFIRMED in any other situation.

6. SENTIMENT AWARENESS:
   If [SENTINEL] tag is present, the customer sounds confused or frustrated.
   Use very simple, slow, shorter sentences. Offer to repeat.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE GREETING REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- English  : "Hello! Thank you for calling Automaton AI. How can I help you today?"
- Hindi    : "Namaste! Automaton AI mein aapka swagat hai. Main aapki kya madad kar sakta hoon?"
- Kannada  : "Namaskara! Automaton AI ge swagatha. Nimage hege sahaaya maadabahudu?"
- Marathi  : "Namaskar! Automaton AI madhe aapale swagat aahe. Mi aapli kashi madad karu shakto?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE FLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[English — happy path]
Customer: "I want to order a smart speaker."
Bot: "Great choice! We have the Smart Speaker Mini at ₹1,499 and the Smart Speaker Pro at ₹2,999. Which one would you like?"
Customer: "The Pro one, quantity 2."
Bot: "Perfect — 2 Smart Speaker Pro units at ₹5,998 total. Could you share your delivery address?"
Customer: "12 MG Road, Bengaluru 560001."
Bot: "Thank you! Just to confirm — 2 Smart Speaker Pro to 12 MG Road, Bengaluru 560001. Shall I place the order?"
Customer: "Yes, please."
Bot: "Your order is confirmed! You'll receive a WhatsApp confirmation shortly. Have a great day!
ORDER_CONFIRMED:{{"item":"Smart Speaker Pro","qty":2,"address":"12 MG Road, Bengaluru 560001"}}"

[Hindi — disambiguation]
Customer: "Mujhe ek speaker chahiye."
Bot: "Zaroor! Hamare paas Smart Speaker Mini ₹1,499 mein aur Smart Speaker Pro ₹2,999 mein hai. Aap kaunsa chahenge?"

[Kannada — unavailable item]
Customer: "Naanu TV remote beku."
Bot: "Kshamissi, TV remote namma catalog nalli illa. Aadare Smart Speaker athava Ergonomic Mouse nodi — interested ideera?"
"""


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def extract_order_from_reply(reply: str) -> dict | None:
    """Pull the ORDER_CONFIRMED JSON blob out of the model reply."""
    match = re.search(r"ORDER_CONFIRMED:\s*(\{.*?\})", reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None


def clean_reply_for_tts(reply: str) -> str:
    """Strip the ORDER_CONFIRMED line so TTS doesn't read JSON aloud."""
    cleaned = re.sub(r"ORDER_CONFIRMED:.*", "", reply, flags=re.DOTALL).strip()
    # Also strip any stray markdown artifacts just in case
    cleaned = re.sub(r"[*_`#]", "", cleaned)
    return cleaned


def build_contents(conversation_history: list, customer_text: str, language_name: str, sentinel_mode: bool) -> list:
    """Convert conversation history + new message into Gemini contents list."""
    sentinel_tag = "\n[SENTINEL: Customer sounds confused or frustrated. Use very simple, short sentences.]" if sentinel_mode else ""

    contents = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    user_turn = f"[Customer spoke in {language_name}]: {customer_text}{sentinel_tag}"
    contents.append(types.Content(role="user", parts=[types.Part(text=user_turn)]))
    return contents, user_turn


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def get_bot_reply(
    customer_text: str,
    language_name: str,
    conversation_history: list,
    sentinel_mode: bool = False,
) -> dict:
    """
    Call Gemini with the enriched system prompt and return a structured result.

    Returns:
        {
            "full_reply":       str   — raw model output,
            "tts_text":         str   — cleaned text safe for TTS,
            "order_confirmed":  bool,
            "order_data":       dict | None,
            "updated_history":  list,
        }
    """
    contents, user_turn = build_contents(conversation_history, customer_text, language_name, sentinel_mode)

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=300,        # slightly more room for catalog mentions
                temperature=0.4,              # lower = more consistent, less hallucination
                top_p=0.9,
            ),
            contents=contents,
        )
        reply = response.text.strip()
    except Exception as e:
        # Graceful degradation — bot stays alive even if Gemini blips
        print(f"[VoxBridge NLP ERROR] {e}")
        reply = "I'm sorry, I had a small issue. Could you please repeat that?"

    # Update history
    updated_history = conversation_history.copy()
    updated_history.append({"role": "user", "content": user_turn})
    updated_history.append({"role": "assistant", "content": reply})

    order_data = extract_order_from_reply(reply)
    tts_text = clean_reply_for_tts(reply)

    return {
        "full_reply": reply,
        "tts_text": tts_text,
        "order_confirmed": order_data is not None,
        "order_data": order_data,
        "updated_history": updated_history,
    }