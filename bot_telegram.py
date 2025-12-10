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


def interactive_wallet_setup ( wallet_instance: Any, wallets: List [ str ] ) -> bool:
    """
    Starts an interactive bot polling session.
    Verifies passphrase and prints config status Before/After.
    """
    if not bot or not TELEGRAM_CHAT_ID:
        print ( "Telegram bot not configured for interactive setup." )
        return False

    # --- [CHECK 1] PRINT BEFORE UPDATE ---
    print ( "\n--------- CHECKING CONFIG FILE (BEFORE) ---------" )
    try:
        with open ( CONFIG_FILE, 'r' ) as f:
            data = json.load ( f )
            print ( f"Current WALLET_ID:         {data.get ( 'WALLET_ID' )}" )
            print ( f"Current WALLET_PASSPHRASE: {data.get ( 'WALLET_PASSPHRASE' )}" )
    except Exception as e:
        print ( f"Could not read config: {e}" )
    print ( "-------------------------------------------------\n" )
    # -------------------------------------------------------

    # 1. Construct and send the prompt
    if wallets:
        wallet_list_str = "\n".join ( [ f"- <code>{w}</code>" for w in wallets ] )
        intro_text = f"The following wallets on your node:\n{wallet_list_str}"
    else:
        intro_text = "<b>Could not automatically list wallets.</b>"

    msg_text = (
        f"<b>⚠️ TeleShake Setup Required ⚠️</b>\n\n"
        f"{intro_text}\n\n"
        f"Input <b>Wallet</b> and <b>Passphrase</b> separated by a colon (:).\n"
        f"<b>(Response required within 5 minutes)</b>\n"
        f"<i>Example:</i>\n<code>skywirex:secretpass123</code>"
    )

    try:
        bot.send_message ( TELEGRAM_CHAT_ID, msg_text, parse_mode="HTML" )
        print ( "Waiting for user input via Telegram (2-minute timeout)..." )
    except Exception as e:
        print ( f"Error sending setup message: {e}" )
        return False

    status = [ False ]

    # 2. Define the handler for the user's response
    @bot.message_handler ( func=lambda m: str ( m.chat.id ) == str ( TELEGRAM_CHAT_ID ) )
    def handle_wallet_selection ( message ):
        text = message.text.strip ()
        parts = text.split ( ':', 1 )

        if len ( parts ) < 2:
            bot.reply_to ( message, "❌ Invalid format. Please enter: <code>WalletID:Passphrase</code>",
                           parse_mode="HTML" )
            return

        wallet_id = parts [ 0 ].strip ()
        passphrase = parts [ 1 ].strip ()

        bot.reply_to ( message, "🔐 Verifying passphrase...", parse_mode="HTML" )

        # --- VERIFICATION ---
        try:
            result = wallet_instance.unlock_wallet ( passphrase=passphrase, id=wallet_id )
            if result.get ( 'success' ) is not True:
                bot.reply_to ( message, f"❌ <b>Access Denied.</b>\nPassphrase incorrect for '{wallet_id}'. Try again.",
                               parse_mode="HTML" )
                return
        except Exception as e:
            bot.reply_to ( message, f"❌ <b>Node Error:</b> {e}", parse_mode="HTML" )
            return
            # --------------------------

        # 3. Update config.json
        try:
            current_config = load_config ()
            current_config [ 'WALLET_ID' ] = wallet_id
            current_config [ 'WALLET_PASSPHRASE' ] = passphrase

            with open ( CONFIG_FILE, 'w' ) as f:
                json.dump ( current_config, f, indent=2 )

            # --- [CHECK 2] PRINT AFTER UPDATE ---
            print ( "\n--------- CHECKING CONFIG FILE (AFTER) ---------" )
            with open ( CONFIG_FILE, 'r' ) as f:
                new_data = json.load ( f )
            # ------------------------------------------------------

            bot.reply_to ( message, f"✅ <b>Updated!</b>\n\nWallet: <b>{wallet_id}</b>\n\n ⏳ Waiting ...", parse_mode="HTML" )

            status [ 0 ] = True
            bot.stop_polling ()

        except Exception as e:
            bot.reply_to ( message, f"Error saving config: {e}" )
            status [ 0 ] = False

    # 4. Start polling
    try:
        bot.polling ( timeout=300 )
    except Exception as e:
        print ( f"Polling stopped: {e}" )

    return status [ 0 ]