from datetime import datetime
from html import escape

# Import bot functions and utility for loading config
from bot_telegram import send_telegram_message, interactive_wallet_setup, load_config

# Import existing utils
from name_manager import (
    WALLET, HSD, HandshakeNameManager
)

CONFIG_FILE = 'config.json'


def html_escape(value):
    return escape(str(value), quote=False)


def load_config_mapping():
    config = load_config()
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a JSON object, got {type(config).__name__}")
    return config


def main ():
    """Run a single cycle – designed to be called by a script"""

    # Instantiate API clients (needed early for setup/verification)
    wallet = WALLET ()
    hsd = HSD ()

    # --- STEP 1: Load & Verify Existing Config ---
    try:
        config = load_config_mapping ()
    except Exception as e:
        print ( f">>> Config Status: Could not load config: {e}" )
        send_telegram_message (
            f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n"
            f"<b>Config load FAILED.</b>\n"
            f"Error details: <code>{html_escape ( e )}</code>\n\n"
            f"Initiating interactive setup via Telegram now.",
            parse_mode="HTML"
        )
        config = { }
    current_wallet_id = config.get ( 'WALLET_ID', '' )
    current_passphrase = config.get ( 'WALLET_PASSPHRASE', '' )

    setup_needed = False

    # 1. Check if ID is missing or default
    if current_wallet_id in [ None, "", "primary" ]:
        print ( ">>> Config Status: Wallet ID not set." )
        setup_needed = True

    # 2. If ID exists, check if Passphrase is valid by trying to unlock
    else:
        print ( f">>> Config Status: Found Wallet ID '{current_wallet_id}'. Verifying passphrase..." )
        try:
            # Attempt to unlock using the method
            result = wallet.unlock_wallet ( passphrase=current_passphrase, id=current_wallet_id, timeout=5 )

            if result.get ( 'success' ) is True:
                print ( ">>> ✅ Passphrase verified successfully." )
            else:
                error_message = f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n" \
                                f"<b>Wallet verification FAILED.</b>\n" \
                                f"Passphrase or wallet is incorrect.\n\n"

                print ( ">>> ❌ Passphrase verification FAILED. stored passphrase is incorrect." )
                send_telegram_message ( error_message, parse_mode="HTML" )  # Send alert to Telegram

                setup_needed = True

        except Exception as e:
            error_message = f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n" \
                            f"<b>Node Connection/Verification ERROR.</b>\n" \
                            f"Could not verify wallet credentials for '<code>{html_escape ( current_wallet_id )}</code>'.\n\n" \
                            f"Error details: <code>{html_escape ( e )}</code>\n\n" \
                            f"Initiating interactive setup via Telegram now."

            print ( f">>> ⚠️ Error connecting to node to verify wallet: {e}" )
            send_telegram_message ( error_message, parse_mode="HTML" )  # Send alert to Telegram

            setup_needed = True

    # --- STEP 2: Interactive Setup (If needed) ---
    if setup_needed:
        print ( ">>> Initiating interactive setup via Telegram..." )

        # Get list of available wallets
        try:
            wallets = wallet.list_wallets ()
        except:
            wallets = [ ]

        # Start Telegram interaction
        setup_successful = interactive_wallet_setup ( wallet, wallets )

        if setup_successful:
            print ( ">>> Configuration successfully updated. Reloading config..." )
            # Reload config to ensure HandshakeNameManager reads the latest data on instantiation
            try:
                config = load_config_mapping ()
            except Exception as e:
                print ( f">>> Could not reload config after setup: {e}" )
                send_telegram_message (
                    f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n"
                    f"<b>Config reload FAILED after setup.</b>\n"
                    f"Error: <code>{html_escape ( e )}</code>\n\n"
                    f"Exiting cycle.",
                    parse_mode="HTML"
                )
                return
        else:
            print ( ">>> Interactive setup failed or timed out. Exiting cycle." )
            return  # Stop execution if we don't have a valid wallet

    # --- STEP 3: Manager Instantiation & Final Check ---
    # This block executes if setup passed or wasn't needed.
    try:
        # Instantiating the manager loads the latest config and runs the initial wallet existence check.
        manager = HandshakeNameManager (
            config_path=CONFIG_FILE,
            wallet=wallet,
            hsd=hsd
        )
    except Exception as e:
        error_message = f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n" \
                        f"<b>Wallet Manager Initialization FAILED.</b>\n" \
                        f"Could not initialize HandshakeNameManager (e.g., wallet check failed, or bad config).\n" \
                        f"Error: <code>{html_escape ( e )}</code>\n\n" \
                        f"Exiting cycle."
        print ( f">>> ❌ Manager Initialization FAILED: {e}" )
        send_telegram_message ( error_message, parse_mode="HTML" )
        return

    # --- STEP 4: Standard Logic (Using Manager) ---
    try:
        # Check wallet is now done inside HandshakeNameManager.__init__

        manager.fetch_and_save_names ()
        renewed_names = manager.renew_expiring_names ()
        info = manager.get_status_info ()
        soonest_expiring = manager.get_soonest_expiring_name ()

        # === Build the message ===
        message_lines = [ f"<b>TeleShake Update ({datetime.now ().strftime ( '%Y-%m-%d %H:%M:%S' )})</b>",
                          "\n<b>INFO:</b>",
                          f"Account: <code>{html_escape ( info.get ( 'account', 'Unknown' ) )}</code> | Height: <code>{html_escape ( info.get ( 'block_height', 'Unknown' ) )}</code>",
                          f"Balance: <code>{html_escape ( info.get ( 'balance', 'Unknown' ) )} HNS</code> | Name: <code>{html_escape ( info.get ( 'names_in_wallet', 'Unknown' ) )}</code>",
                          f"Address: <code>{html_escape ( info.get ( 'full_receiving_address', 'Unknown' ) )}</code>",
                          "\n<b>SOONEST EXPIRING NAME:</b>" ]

        if soonest_expiring [ "name" ]:
            message_lines.append ( f"Name: <code>{html_escape ( soonest_expiring [ 'name' ] )}</code>" )
            message_lines.append ( f"Expires: <code>{html_escape ( soonest_expiring [ 'expiration_date' ] )}</code>" )
            message_lines.append ( f"Days until expiration: <code>{html_escape ( soonest_expiring [ 'days_until_expire' ] )}</code>" )
        else:
            message_lines.append ( "No names found" )

        message_lines.append ( f"\n<b>RENEWAL (in <code>{manager.threshold_days}</code> DAYS):</b>" )
        if renewed_names:
            message_lines.append ( "Renewed the following names:" )
            message_lines.extend ( [ f"- <code>{html_escape ( name )}</code>" for name in renewed_names ] )
        else:
            message_lines.append ( "No names required renewal" )

        message_lines.append("\n<b>🙏 SUPPORT & DONATE:</b>")
        message_lines.append("HNS: <code>hs1qwrsfl8vkjqxfdncfn00dtzvpcdcj3rlj70zg3m</code>")


        message = "\n".join ( message_lines )
        send_telegram_message ( message, parse_mode="HTML" )
        print ( f"{datetime.now ()} - Cycle completed successfully." )

    except Exception as e:
        error_message = f"<b>Teleshake ERROR ({datetime.now ().strftime ( '%Y-%m-%d %H:%M' )}):</b>\n{html_escape ( e )}"
        print ( f"Error: {e}" )
        try:
            send_telegram_message ( error_message, parse_mode="HTML" )
        except:
            pass


if __name__ == "__main__":
    main ()
