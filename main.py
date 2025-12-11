from datetime import datetime

# Import bot functions and utility for loading config
from bot_telegram import send_telegram_message, interactive_wallet_setup, load_config

# Import existing utils
from name_manager import (
    WALLET, HSD, HandshakeNameManager
)

CONFIG_FILE = 'config.json'


def main ():
    """Run a single cycle – designed to be called by a script"""

    # Instantiate API clients (needed early for setup/verification)
    wallet = WALLET ()
    hsd = HSD ()

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
                            f"Could not verify wallet credentials for '<code>{current_wallet_id}</code>'.\n\n" \
                            f"Error details: <code>{str ( e )}</code>\n\n" \
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
            config = load_config ()
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
                        f"Error: <code>{str ( e )}</code>\n\n" \
                        f"Exiting cycle."
        print ( f">>> ❌ Manager Initialization FAILED: {e}" )
        send_telegram_message ( error_message, parse_mode="HTML" )
        return

    # --- STEP 4: Standard Logic (Using Manager) ---
    try:
        # Check wallet is now done inside HandshakeNameManager.__init__

        manager.fetch_and_save_names ()
        renewed_names = manager.renew_expiring_names ()  # New method name
        info = manager.get_status_info ()  # New method name
        soonest_expiring = manager.get_soonest_expiring_name ()  # New method name

        # === Build the message ===
        message_lines = [ f"<b>TeleShake Update ({datetime.now ().strftime ( '%Y-%m-%d %H:%M:%S' )})</b>",
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

        message_lines.append("\n<b>🙏 SUPPORT & DONATE:</b>")
        message_lines.append("HNS: <code>hs1qwrsfl8vkjqxfdncfn00dtzvpcdcj3rlj70zg3m</code>")


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