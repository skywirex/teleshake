import sys
from datetime import datetime
import importlib

# Import bot functions and utility for loading config
from bot_telegram import send_telegram_message, interactive_wallet_setup, load_config

# Import existing utils
from utils import (
    WALLET, HSD, check_wallet_existing, fetch_and_save_names, renew_names,
    get_wallet_and_node_info, find_soonest_expiring_name
)

CONFIG_FILE = 'config.json'


def main ():
    """Run a single cycle – designed to be called by a script"""

    # Instantiate classes
    wallet = WALLET ()

    # --- STEP 1: Load & Verify Existing Config ---
    config = load_config ()
    current_wallet_id = config.get ( 'WALLET_ID', '' )
    current_passphrase = config.get ( 'WALLET_PASSPHRASE', '' )

    setup_needed = False

    # 1. Check if ID is missing or default
    if current_wallet_id in [ None, "", "primary" ]:
        print ( ">>> Config Status: Wallet ID not set." )
        setup_needed = True

    # 2. If ID exists, check if Passphrase is valid by trying to unlock
    else:
        print(f">>> Config Status: Found Wallet ID '{current_wallet_id}'. Verifying passphrase...")
        try:
            # Attempt to unlock using the method added to utils.py
            # Using a short timeout just for verification
            result = wallet.unlock_wallet(passphrase=current_passphrase, id=current_wallet_id, timeout=5)

            if result.get('success') is True:
                print(">>> ✅ Passphrase verified successfully.")
            else:
                error_message = f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n" \
                                f"<b>Wallet verification FAILED.</b>\n" \
                                f"Passphrase or wallet is incorrect.\n\n"

                print(">>> ❌ Passphrase verification FAILED. stored passphrase is incorrect.")
                send_telegram_message(error_message, parse_mode="HTML") # Send alert to Telegram

                setup_needed = True

        except Exception as e:
            error_message = f"<b>⚠️ TeleShake ALERT ⚠️</b>\n\n" \
                            f"<b>Node Connection/Verification ERROR.</b>\n" \
                            f"Could not verify wallet credentials for '<code>{current_wallet_id}</code>'.\n\n" \
                            f"Error details: <code>{str(e)}</code>\n\n" \
                            f"Initiating interactive setup via Telegram now."

            print(f">>> ⚠️ Error connecting to node to verify wallet: {e}")
            send_telegram_message(error_message, parse_mode="HTML") # Send alert to Telegram

            setup_needed = True


    # --- STEP 2: Interactive Setup (If needed) ---
    if setup_needed:
        print ( ">>> Initiating interactive setup via Telegram..." )

        # Get list of available wallets
        try:
            wallets = wallet.list_wallets ()
        except:
            wallets = [ ]

        # Start Telegram interaction (Pass 'wallet' instance for verification)
        setup_successful = interactive_wallet_setup ( wallet, wallets )

        if setup_successful:
            print ( ">>> Configuration successfully updated. Reloading config..." )
            config = load_config ()

            # Reload utils module to ensure it picks up any new global vars if necessary
            if 'utils' in sys.modules:
                importlib.reload ( sys.modules [ 'utils' ] )
                print ( ">>> utils module reloaded." )

            # Re-instantiate wallet with new config
            wallet = WALLET ()
        else:
            print ( ">>> Interactive setup failed or timed out. Exiting cycle." )
            return  # Stop execution if we don't have a valid wallet

    # --- STEP 3: Standard Logic ---
    # This block executes only if config is valid (old or newly updated)
    try:
        hsd = HSD ()

        # Double check existence
        check_wallet_existing ( wallet )

        fetch_and_save_names ( wallet )
        renewed_names = renew_names ( wallet )
        info = get_wallet_and_node_info ( wallet, hsd )
        soonest_expiring = find_soonest_expiring_name ()

        # === Build the message ===
        message_lines = [ f"<b>Teleshake Update ({datetime.now ().strftime ( '%Y-%m-%d %H:%M:%S' )})</b>",
                          "\n<b>INFO:</b>",
                          f"Account: <code>{info [ 'account' ]}</code> | Height: <code>{info [ 'block_height' ]}</code>",
                          f"Balance: <code>{info [ 'balance' ]} HNS</code>",
                          f"Address: <code>{info [ 'full_receiving_address' ]}</code>",
                          "\n<b>SOONEST EXPIRING NAME:</b>" ]

        if soonest_expiring [ "name" ]:
            message_lines.append ( f"Name: <code>{soonest_expiring [ 'name' ]}</code>" )
            message_lines.append ( f"Expires: <code>{soonest_expiring [ 'expiration_date' ]}</code>" )
            message_lines.append ( f"Days until expiration: <code>{soonest_expiring [ 'days_until_expire' ]}</code>" )
        else:
            message_lines.append ( "No names found" )

        message_lines.append ( "\n<b>RENEWAL:</b>" )
        if renewed_names:
            message_lines.append ( "Renewed the following names:" )
            message_lines.extend ( [ f"- <code>{name}</code>" for name in renewed_names ] )
        else:
            message_lines.append ( "No names required renewal" )

        message = "\n".join ( message_lines )
        send_telegram_message ( message, parse_mode="HTML" )
        print ( f"{datetime.now ()} - Cycle completed successfully." )

    except Exception as e:
        error_message = f"<b>Teleshake ERROR ({datetime.now ().strftime ( '%Y-%m-%d %H:%M' )}):</b>\n{str ( e )}"
        print ( f"Error: {e}" )
        try:
            send_telegram_message ( error_message, parse_mode="HTML" )
        except:
            pass


if __name__ == "__main__":
    main ()