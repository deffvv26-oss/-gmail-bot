import os
import time
import pickle
import asyncio

from telegram import Bot
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ======================
# CONFIG
# ======================

BOT_TOKEN = "8977835440:AAFOUwppmY689eg93VEDOfwonmcceNJ76Oc"
CHAT_ID = 123456789  # replace with your Telegram ID

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

bot = Bot(token=BOT_TOKEN)

seen_ids = set()

# ======================
# GMAIL AUTH (CLOUD SAFE)
# ======================

def get_service():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


service = get_service()

# ======================
# EMAIL FUNCTIONS
# ======================

def fetch_emails():
    results = service.users().messages().list(
        userId="me",
        maxResults=5
    ).execute()

    return results.get("messages", [])


def get_email_data(msg_id):
    msg = service.users().messages().get(
        userId="me",
        id=msg_id
    ).execute()

    snippet = msg.get("snippet", "")
    headers = msg["payload"]["headers"]

    sender = ""
    subject = ""

    for h in headers:
        if h["name"] == "From":
            sender = h["value"]
        if h["name"] == "Subject":
            subject = h["value"]

    return sender, subject, snippet


# ======================
# TELEGRAM SEND (FIXED)
# ======================

async def send_message(text):
    await bot.send_message(chat_id=CHAT_ID, text=text)


# ======================
# FILTER (SMART KEYWORDS)
# ======================

def is_youngla_email(text):
    keywords = [
        "youngla",
        "young la",
        "young-la",
        "youngla.com",
        "order",
        "shipping",
        "shipment",
        "delivered",
        "tracking"
    ]

    text = text.lower()
    return any(k in text for k in keywords)


# ======================
# MAIN LOOP
# ======================

async def check_loop():
    global seen_ids

    print("🤖 YoungLA tracker running...")

    while True:
        try:
            messages = fetch_emails()

            for m in messages:
                msg_id = m["id"]

                if msg_id in seen_ids:
                    continue

                seen_ids.add(msg_id)

                sender, subject, snippet = get_email_data(msg_id)

                full_text = f"{sender} {subject} {snippet}"

                if is_youngla_email(full_text):
                    await send_message(
                        f"📦 YoungLA Email\n\nFrom: {sender}\n\n{subject}\n\n{snippet}"
                    )

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(60)


# ======================
# RUN
# ======================

if __name__ == "__main__":
    asyncio.run(check_loop())
