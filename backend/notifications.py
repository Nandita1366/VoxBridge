from twilio.rest import Client
from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    TWILIO_WHATSAPP_FROM,
)


def send_order_confirmation_whatsapp(to_phone: str, order: dict, language: str) -> bool:
    """
    Sends WhatsApp confirmation message after order is placed.
    Works with Twilio's WhatsApp sandbox.
    """
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        lang_messages = {
            "hi": f"✅ Aapka order confirm ho gaya!\n📦 Item: {order['item']}\n🔢 Quantity: {order['qty']}\n📍 Address: {order['address']}\n\nAutomaton AI ki taraf se shukriya! 🙏",
            "kn": f"✅ Nimma order confirm aagide!\n📦 Item: {order['item']}\n🔢 Quantity: {order['qty']}\n📍 Address: {order['address']}\n\nAutomaton AI dinda dhanyavadagalu! 🙏",
            "mr": f"✅ Tumcha order confirm zala!\n📦 Item: {order['item']}\n🔢 Quantity: {order['qty']}\n📍 Address: {order['address']}\n\nAutomaton AI kadeun dhanyawad! 🙏",
            "en": f"✅ Your order is confirmed!\n📦 Item: {order['item']}\n🔢 Quantity: {order['qty']}\n📍 Address: {order['address']}\n\nThank you for choosing Automaton AI! 🙏",
        }
        body = lang_messages.get(language, lang_messages["en"])

        to_whatsapp = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone

        client.messages.create(body=body, from_=TWILIO_WHATSAPP_FROM, to=to_whatsapp)
        return True
    except Exception as e:
        print(f"[WhatsApp Error] {e}")
        return False


def send_sms_fallback(to_phone: str, order: dict) -> bool:
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"✅ Order Confirmed! Item: {order['item']}, Qty: {order['qty']}, Address: {order['address']} — Automaton AI",
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone,
        )
        return True
    except Exception as e:
        print(f"[SMS Error] {e}")
        return False
