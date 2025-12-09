import sys
from datetime import datetime
import importlib

# Import bot functions and utility for loading config
from bot_telegram import send_telegram_message, interactive_wallet_setup, load_config

# Import existing utils (Assuming these exist as per your original file)
from utils import (
    WALLET, HSD, check_wallet_existing, fetch_and_save_names, renew_names,
    get_wallet_and_node_info, find_soonest_expiring_name
)

CONFIG_FILE = 'config.json'

def main ():
    """Run a single cycle – designed to be called by a script"""
    wallet = WALLET ()
    # --- STEP 1: Check Configuration & Interactive Setup ---
    config = { }
    setup_successful = False  # Flag to track if the interactive setup completed successfully

    try:
        config = load_config ()
        current_wallet_id = config.get ( 'WALLET_ID', '' )

        # Check if setup is needed (if wallet is empty, 'primary', or None)
        if current_wallet_id in [ None, "", "primary" ]:
            print ( ">>> Wallet ID not configured or set to default ('primary'). Initiating interactive setup..." )

            wallets = wallet.list_wallets ()

            # Start Telegram interaction and capture success
            setup_successful = interactive_wallet_setup ( wallets )

            if setup_successful:
                # Reload configuration file after successful update by the bot
                # This ensures the standard logic runs immediately with the new config.
                print ( ">>> Configuration successfully updated. Reloading and restarting cycle now..." )
                config = load_config ()

                # FIX: Reload the utils module
                if 'utils' in sys.modules:
                    importlib.reload ( sys.modules [ 'utils' ] )
                    print ( ">>> utils module reloaded to use new WALLET_ID." )
            else:
                print (
                    ">>> Interactive setup failed or timed out. Proceeding with existing config or default settings." )


    except Exception as e:
        print ( f"Setup Error during config load or interactive process: {e}" )

    # --- STEP 2: Standard Logic (Existing Code) ---
    # This block executes immediately after the setup block, completing the "restart"
    try:
        # Instantiate classes
        wallet, hsd = WALLET (), HSD ()
        check_wallet_existing ( wallet )  # Will fail fast if wallet is missing

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