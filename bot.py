import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv ()

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv ( 'TELEGRAM_BOT_TOKEN' )
TELEGRAM_CHAT_ID = os.getenv ( 'TELEGRAM_CHAT_ID' )


def send_telegram_message ( message: str ) -> None:
    """Send a message via Telegram bot.

    Args:
        message (str): The message to send.

    Returns:
        None: Prints success or failure status.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print ( "Telegram bot token or chat ID not configured in .env" )
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post ( url, json=payload )
        response.raise_for_status ()
        print ( "Telegram message sent successfully" )
    except requests.RequestException as e:
        print ( f"Failed to send Telegram message: {e}" )