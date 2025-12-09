import json
import os
import telebot  # pyTelegramBotAPI
from typing import List, Dict, Any

# Load configuration from config.json
CONFIG_FILE = 'config.json'


def load_config () -> Dict [ str, Any ]:
    """Loads and returns the current configuration from config.json."""
    if not os.path.exists ( CONFIG_FILE ):
        # Allow bot to start without config if called directly, but raise for main script
        return { }
    with open ( CONFIG_FILE, 'r' ) as f:
        return json.load ( f )


# Load configuration and initialize bot
try:
    config = load_config ()
    TELEGRAM_BOT_TOKEN = config.get ( 'TELEGRAM_BOT_TOKEN', '' )
    TELEGRAM_CHAT_ID = config.get ( 'TELEGRAM_CHAT_ID', '' )
    bot = telebot.TeleBot ( TELEGRAM_BOT_TOKEN ) if TELEGRAM_BOT_TOKEN else None
except Exception as e:
    print ( f"Error loading initial config for bot: {e}" )
    TELEGRAM_BOT_TOKEN = ''
    TELEGRAM_CHAT_ID = ''
    bot = None


def send_telegram_message ( message: str, parse_mode: str = None ) -> None:
    """Send a message via Telegram bot (Standard Alert)."""
    if not bot or not TELEGRAM_CHAT_ID:
        print ( "Telegram configuration missing." )
        return

    try:
        bot.send_message ( TELEGRAM_CHAT_ID, message, parse_mode=parse_mode )
        print ( "Telegram message sent successfully" )
    except Exception as e:
        print ( f"Failed to send Telegram message: {e}" )


def interactive_wallet_setup ( wallets: List [ str ] ) -> bool:
    """
    Starts an interactive bot polling session.

    Returns:
        bool: True if config was successfully updated, False otherwise (e.g., timeout).
    """
    if not bot or not TELEGRAM_CHAT_ID:
        print ( "Telegram bot not configured for interactive setup." )
        return False

    # 1. Construct and send the prompt to the user
    if wallets:
        wallet_list_str = "\n".join ( [ f"- <code>{w}</code>" for w in wallets ] )
        intro_text = f"The following wallets on your node:\n{wallet_list_str}"
    else:
        intro_text = "<b>Could not automatically list wallets.</b>"

    msg_text = (
        f"<b>⚠️ TeleShake Setup Required ⚠️</b>\n\n"
        f"{intro_text}\n\n"
        f"Input <b>Wallet</b> and <b>Passphrase</b> separated by a colon (:).\n"
        # --- Notification Added and Timeout Updated ---
        f"<b>(Response required within 2 minutes)</b>\n"
        f"<i>Example:</i>\n<code>skywirex:secretpass123</code>"
        # ----------------------------------------------
    )

    try:
        bot.send_message ( TELEGRAM_CHAT_ID, msg_text, parse_mode="HTML" )
        print ( "Waiting for user input via Telegram (2-minute timeout)..." )
    except Exception as e:
        print ( f"Error sending setup message: {e}" )
        return False

    # Use a list to hold the success status so it can be modified inside the nested function
    status = [ False ]

    # 2. Define the handler for the user's response
    @bot.message_handler ( func=lambda m: str ( m.chat.id ) == str ( TELEGRAM_CHAT_ID ) )
    def handle_wallet_selection ( message ):
        # Note: The 'nonlocal' keyword is required if you are using Python 3 and are not relying on a mutable object like a list.
        # Since we use status[0], which is Python 2 and 3 compatible, 'nonlocal' is not strictly necessary here,
        # but adding it for robustness if the code environment were to change.
        # However, for the provided code context and simplicity, we rely on the mutable list `status`.

        text = message.text.strip ()
        parts = text.split ( ':', 1 )

        if len ( parts ) < 2:
            bot.reply_to ( message, "❌ Invalid format. Please enter: <code>WalletID:Passphrase</code>",
                           parse_mode="HTML" )
            return

        wallet_id = parts [ 0 ].strip ()
        passphrase = parts [ 1 ].strip ()

        # 3. Update config.json (Overwrites the current JSON configuration file)
        try:
            current_config = load_config ()
            current_config [ 'WALLET_ID' ] = wallet_id
            current_config [ 'WALLET_PASSPHRASE' ] = passphrase

            with open ( CONFIG_FILE, 'w' ) as f:
                json.dump ( current_config, f, indent=2 )

            bot.reply_to ( message,
                           f"✅ Updated!\n\nWallet: <b>{wallet_id}</b>\n\n⏳ Waiting ...",
                           parse_mode="HTML" )
            print ( f"Config updated with wallet: {wallet_id}" )

            # Set success flag and stop polling
            status [ 0 ] = True
            bot.stop_polling ()

        except Exception as e:
            bot.reply_to ( message, f"Error saving config: {e}" )
            status [ 0 ] = False  # Ensure status is False on error

    # 4. Start polling (blocking) until stop_polling is called or timeout occurs
    try:
        bot.polling ( timeout=120 )
        print ( "Telegram polling finished." )
    except Exception as e:
        print ( f"Telegram polling stopped (possibly due to timeout): {e}" )

    return status [ 0 ]  # Return the final success status