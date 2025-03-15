import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv
from api.hsd import HSD
from api.wallet import WALLET
from bot import send_telegram_message  # Import from bot.py

# Load environment variables
load_dotenv ()

# Renewal configuration from .env
RENEWAL_THRESHOLD_DAYS = int ( os.getenv ( 'RENEWAL_THRESHOLD_DAYS', 30 ) )
LOOP_PERIOD_SECONDS = int(os.getenv('LOOP_PERIOD_SECONDS', 3600))  # Default to 1 hour (3600 seconds)

# Wallet configuration from .env
WALLET_ID = os.getenv ( 'WALLET_ID', 'primary' )
WALLET_PASSPHRASE = os.getenv ( 'WALLET_PASSPHRASE', '' )
WALLET_MNEMONIC = os.getenv ( 'WALLET_MNEMONIC', '' )

# JSON file to store name data
NAMES_JSON_FILE = 'wallet_names.json'


def check_and_create_wallet ( wallet: WALLET ) -> None:
    """Check if wallet exists, create it if it doesn't."""
    response = wallet.get_wallet_info ( WALLET_ID )
    if "error" in response:
        print ( f"Wallet '{WALLET_ID}' does not exist or is inaccessible. Creating it..." )
        create_response = wallet.create_wallet (
            passphrase=WALLET_PASSPHRASE,
            id=WALLET_ID,
            mnemonic=WALLET_MNEMONIC
        )
        if "error" in create_response:
            raise RuntimeError ( f"Failed to create wallet: {create_response [ 'error' ]}" )
        print ( f"Wallet '{WALLET_ID}' created successfully" )
    else:
        print ( f"Wallet '{WALLET_ID}' already exists" )


def get_expiration_date ( name_info: Dict [ str, Any ] ) -> datetime:
    """Extract expiration date from name info using daysUntilExpire."""
    stats = name_info.get ( "stats", { } )
    days_until_expire = stats.get ( "daysUntilExpire", None )

    if days_until_expire is None:
        # Fallback if daysUntilExpire is missing
        print ( f"Warning: No daysUntilExpire for '{name_info [ 'name' ]}'; assuming distant future expiration" )
        return datetime.now () + timedelta ( days=365 * 2 )  # Default to 2 years

    expiration_date = datetime.now () + timedelta ( days=days_until_expire )
    return expiration_date


def fetch_and_save_names ( wallet: WALLET ) -> None:
    """Fetch owned names and save to JSON file."""
    response = wallet.get_wallet_names_own ( WALLET_ID )
    if "error" in response:
        raise RuntimeError ( f"Failed to fetch wallet names: {response [ 'error' ]}" )

    names_data = { }
    for name_info in response:
        name = name_info [ "name" ]
        try:
            expiration_date = get_expiration_date ( name_info )
            renewal_height = name_info.get ( "renewal", 0 )
            names_data [ name ] = {
                "expiration_date": expiration_date.isoformat (),
                "days_until_expire": name_info.get ( "stats", { } ).get ( "daysUntilExpire", None )
            }
        except Exception as e:
            print ( f"Error processing name '{name}': {str ( e )}" )

    with open ( NAMES_JSON_FILE, 'w' ) as f:
        json.dump ( names_data, f, indent=4 )
    print ( f"Names data saved to {NAMES_JSON_FILE}" )


def renew_names ( wallet: WALLET ) -> list:
    """Read names from JSON, renew if expiring soon using send_renew, and return renewed names."""
    if not os.path.exists ( NAMES_JSON_FILE ):
        raise FileNotFoundError ( f"{NAMES_JSON_FILE} not found. Run fetch_and_save_names first." )

    with open ( NAMES_JSON_FILE, 'r' ) as f:
        names_data = json.load ( f )

    current_date = datetime.now ()
    threshold_date = current_date + timedelta ( days=RENEWAL_THRESHOLD_DAYS )
    renewed_names = [ ]

    for name, data in names_data.items ():
        expiration_date = datetime.fromisoformat ( data [ "expiration_date" ] )
        if expiration_date <= threshold_date:
            print ( f"Renewing name '{name}' expiring on {expiration_date}" )
            response = wallet.send_renew (
                id=WALLET_ID,
                passphrase=WALLET_PASSPHRASE,
                name=name,
                sign=True,
                broadcast=True
            )
            if "error" in response:
                print ( f"Failed to renew '{name}': {response [ 'error' ]}" )
            else:
                renewed_names.append ( name )
                print ( f"Successfully renewed '{name}'" )

    return renewed_names


def get_wallet_and_node_info ( wallet: WALLET, hsd: HSD ) -> Dict [ str, Any ]:
    """Fetch wallet and node information for notification."""
    info = { }

    # Current HNS block height using get_info
    node_info = hsd.get_info ()
    info [ "block_height" ] = node_info.get ( "chain", { } ).get ( "height",
                                                                   "Unknown" ) if "error" not in node_info else "Error"

    # Current account using WALLET_ID from .env
    info [ "account" ] = WALLET_ID

    # HNS balance using get_balance with spendable balance calculation
    balance_info = wallet.get_balance(id=WALLET_ID)
    if "error" not in balance_info:
        balance = balance_info
        spendable_balance = (balance.get("unconfirmed", 0) - balance.get("lockedUnconfirmed", 0)) / 1_000_000
        info["balance"] = spendable_balance
    else:
        info["balance"] = "Error"

    # Current receiving address using get_account_info["receiveAddress"]
    account_info = wallet.get_account_info ( id=WALLET_ID )
    info [ "receiving_address" ] = account_info.get ( "receiveAddress",
                                                      "Error" ) if "error" not in account_info else "Error"

    return info


def main ():
    """Main function to manage wallet names and renewals with periodic execution."""
    wallet, hsd = WALLET (), HSD ()
    check_and_create_wallet ( wallet )  # Run once at startup

    while True:
        try:
            fetch_and_save_names ( wallet )
            renewed_names = renew_names ( wallet )
            info = get_wallet_and_node_info ( wallet, hsd )

            message_lines = [ f"Teleshake Update ({datetime.now ().strftime ( '%Y-%m-%d %H:%M:%S' )})" ]

            # Wallet and node info (moved above renewal results)
            message_lines.append ( "\nINFO:" )
            message_lines.append ( f"Block Height: {info [ 'block_height' ]} | Account: {info [ 'account' ]}" )
            message_lines.append ( f"Balance: {info [ 'balance' ]} HNS" )
            message_lines.append ( f"Address: {info [ 'receiving_address' ]}" )

            # Renewal results
            message_lines.append ( "\nRENEWAL:" )
            if renewed_names:
                message_lines.append ( "Renewed the following names:" )
                message_lines.extend ( [ f"- {name}" for name in renewed_names ] )
            else:
                message_lines.append ( "No names required renewal" )

            message = "\n".join ( message_lines )
            send_telegram_message ( message )
            print(f"Notification sent. Sleeping for {LOOP_PERIOD_SECONDS} seconds...")

        except Exception as e:
            print ( f"Error in loop: {e}" )
            send_telegram_message ( f"Error in Handshake Wallet Update: {e}" )

        time.sleep ( LOOP_PERIOD_SECONDS )


if __name__ == "__main__":
    main ()