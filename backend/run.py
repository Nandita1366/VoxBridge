"""
Start the VoxBridge backend with auto ngrok tunnel.
Run: python run.py
"""
import os
from pyngrok import ngrok
import uvicorn
from dotenv import load_dotenv, set_key

load_dotenv()


def start():
    ngrok_token = os.getenv("NGROK_AUTHTOKEN")
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)

    tunnel = ngrok.connect(8000, "http")
    public_url = tunnel.public_url
    print(f"\nPublic URL: {public_url}")
    print(f"Set this in Twilio Voice webhook: {public_url}/voice/inbound\n")

    set_key(".env", "BASE_URL", public_url)
    os.environ["BASE_URL"] = public_url

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    start()
