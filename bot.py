import json
import os
import requests

# Load configuration from config.json
CONFIG_FILE = 'config.json'
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Configuration file {CONFIG_FILE} not found")

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

# Telegram bot configuration from config.json
TELEGRAM_BOT_TOKEN = config.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = config.get('TELEGRAM_CHAT_ID', '')

def send_telegram_message(message: str, parse_mode: str = None) -> None:
    """Send a message via Telegram bot.

    Args:
        message (str): The message to send.
        parse_mode (str, optional): Parse mode for formatting (e.g., 'HTML'). Defaults to None.

    Returns:
        None: Prints success or failure status.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token or chat ID not configured in config.json")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message sent successfully")
    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")


# Test call function
if __name__ == "__main__":
    send_telegram_message("Test message from bot.py", parse_mode="HTML")