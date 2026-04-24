# VoxBridge 🎙️
> Multilingual AI voice order bot for Automaton AI Infosystem

## Features
- 📞 Automated inbound/outbound voice calls via Twilio
- 🌐 Supports English, Hindi, Kannada, Marathi — auto-detected
- 🤖 Claude AI for natural order conversation
- ⚡ Sentinel Mode — detects frustration, adapts automatically
- 📲 WhatsApp confirmation after every order
- 📊 Live ops dashboard with WebSocket real-time feed

## Setup (5 minutes)
```bash
cd backend && pip install -r requirements.txt && python run.py
cd frontend && npm install && npm run dev
```
Set Twilio webhook to the printed ngrok URL + /voice/inbound

## Architecture
Customer → Twilio → FastAPI → Whisper STT → Claude NLP → Google TTS → Twilio
                                          ↓
                              Sentinel Sentiment Guard
                                          ↓
                              PostgreSQL + WhatsApp + React Dashboard

## Tech Stack
Python · FastAPI · Twilio · OpenAI Whisper · Anthropic Claude · Google TTS · React · Recharts · WebSockets
