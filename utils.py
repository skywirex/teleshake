import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from api.hsd import HSD
from api.wallet import WALLET

# Load configuration from config.json
CONFIG_FILE = 'config.json'
if not os.path.exists ( CONFIG_FILE ):
    raise FileNotFoundError ( f"Configuration file {CONFIG_FILE} not found" )

with open ( CONFIG_FILE, 'r' ) as f:
    config = json.load ( f )

# Define global variables from config
RENEWAL_THRESHOLD_DAYS = config.get ( 'RENEWAL_THRESHOLD_DAYS', 30 )
LOOP_PERIOD_SECONDS = config.get ( 'LOOP_PERIOD_SECONDS', 3600 )
WALLET_ID = config.get ( 'WALLET_ID', 'primary' )
WALLET_PASSPHRASE = config.get ( 'WALLET_PASSPHRASE', '' )
NAMES_JSON_FILE = 'wallet_names.json'


def check_wallet_existing(wallet: WALLET) -> None:
    """
    Check if the configured wallet exists.
    If it does NOT exist → log the situation and raise an error.
    This replaces the previous check_and_create_wallet behaviour.
    """
    response = wallet.get_wallet_info(WALLET_ID)

    if "error" in response:
        error_msg = (
            f"Wallet '{WALLET_ID}' does NOT exist. "
            f"Expected wallet ID must be created manually or via a different process.\n"
            f"API error details: {response.get('error', 'unknown')}"
        )
        print(error_msg)
        raise RuntimeError(error_msg)
    else:
        print(f"Wallet '{WALLET_ID}' already exists and is ready.")


def get_expiration_date ( name_info: Dict [ str, Any ] ) -> datetime:
    stats = name_info.get ( "stats", { } )
    days_until_expire = stats.get ( "daysUntilExpire", None )
    if days_until_expire is None:
        print ( f"Warning: No daysUntilExpire for '{name_info [ 'name' ]}'; assuming distant future" )
        return datetime.now () + timedelta ( days=365 * 2 )
    return datetime.now () + timedelta ( days=days_until_expire )


def fetch_and_save_names ( wallet: WALLET ) -> None:
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
                "renewal_height": renewal_height,
                "days_until_expire": name_info.get ( "stats", { } ).get ( "daysUntilExpire", None )
            }
        except Exception as e:
            print ( f"Error processing name '{name}': {str ( e )}" )

    with open ( NAMES_JSON_FILE, 'w' ) as f:
        json.dump ( names_data, f, indent=4 )
    print ( f"Names data saved to {NAMES_JSON_FILE}" )


def renew_names ( wallet: WALLET ) -> List [ str ]:
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
    info = { }
    node_info = hsd.get_info ()
    info [ "block_height" ] = node_info.get ( "chain", { } ).get ( "height",
                                                                   "Unknown" ) if "error" not in node_info else "Error"
    info [ "account" ] = WALLET_ID
    balance_info = wallet.get_balance ( id=WALLET_ID )
    if "error" not in balance_info:
        balance = balance_info
        spendable_balance = (balance.get ( "unconfirmed", 0 ) - balance.get ( "lockedUnconfirmed", 0 )) / 1_000_000
        info [ "balance" ] = spendable_balance
    else:
        info [ "balance" ] = "Error"
    account_info = wallet.get_account_info ( id=WALLET_ID )
    full_address = account_info.get ( "receiveAddress", "Error" ) if "error" not in account_info else "Error"
    info [
        "receiving_address" ] = full_address if full_address == "Error" else f"{full_address [ :6 ]}...{full_address [ -4: ]}"
    info [ "full_receiving_address" ] = full_address
    return info


def find_soonest_expiring_name () -> Dict [ str, Any ]:
    """Find the domain name expiring soonest from wallet_names.json."""
    if not os.path.exists ( NAMES_JSON_FILE ):
        return { "name": None, "expiration_date": None, "days_until_expire": None }

    with open ( NAMES_JSON_FILE, 'r' ) as f:
        names_data = json.load ( f )

    if not names_data:
        return { "name": None, "expiration_date": None, "days_until_expire": None }

    soonest_name = None
    soonest_expiration = None
    for name, data in names_data.items ():
        expiration_date = datetime.fromisoformat ( data [ "expiration_date" ] )
        if soonest_expiration is None or expiration_date < soonest_expiration:
            soonest_name = name
            soonest_expiration = expiration_date

    days_until_expire = (soonest_expiration - datetime.now ()).days if soonest_expiration else None
    return {
        "name": soonest_name,
        "expiration_date": soonest_expiration.strftime ( '%Y-%m-%d %H:%M:%S' ) if soonest_expiration else None,
        "days_until_expire": days_until_expire
    }


# Test functions
if __name__ == "__main__":
    # Mock classes for testing (simplified)
    class MockWallet:
        def get_wallet_info ( self, wallet_id ):
            return { "id": wallet_id }  # Simulate wallet exists

        def create_wallet ( self, passphrase, id, mnemonic ):
            return { "id": id }  # Simulate successful creation

        def get_wallet_names_own ( self, wallet_id ):
            return [
                { "name": "test.hns", "renewal": 123, "stats": { "daysUntilExpire": 10 } }
            ]  # Mock names

        def send_renew ( self, id, passphrase, name, sign, broadcast ):
            return { "success": True }  # Mock successful renewal

        def get_balance ( self, id ):
            return { "unconfirmed": 123500000, "lockedUnconfirmed": 0 }

        def get_account_info ( self, id ):
            return { "receiveAddress": "hs1qmockaddress123" }


    class MockHSD:
        def get_info ( self ):
            return { "chain": { "height": 268271 } }


    def test_check_wallet_existing ():
        print ( "Testing check_and_create_wallet..." )
        wallet = MockWallet ()
        check_wallet_existing ( wallet )
        print ( "Test passed: Wallet check/creation executed" )


    def test_fetch_and_save_names ():
        print ( "Testing fetch_and_save_names..." )
        wallet = MockWallet ()
        fetch_and_save_names ( wallet )
        with open ( NAMES_JSON_FILE, 'r' ) as f:
            data = json.load ( f )
        assert "test.hns" in data, "Name not saved"
        print ( "Test passed: Names fetched and saved" )


    def test_renew_names ():
        print ( "Testing renew_names..." )
        wallet = MockWallet ()
        # Create a mock wallet_names.json
        mock_data = {
            "test.hns": {
                "expiration_date": (datetime.now () + timedelta ( days=5 )).isoformat (),
                "renewal_height": 123,
                "days_until_expire": 5
            }
        }
        with open ( NAMES_JSON_FILE, 'w' ) as f:
            json.dump ( mock_data, f )
        renewed = renew_names ( wallet )
        assert "test.hns" in renewed, "Name not renewed"
        print ( "Test passed: Name renewed" )


    def test_get_wallet_and_node_info ():
        print ( "Testing get_wallet_and_node_info..." )
        wallet = MockWallet ()
        hsd = MockHSD ()
        info = get_wallet_and_node_info ( wallet, hsd )
        assert info [ "block_height" ] == 268271, "Block height mismatch"
        assert info [ "balance" ] == 123.5, "Balance mismatch"
        assert info [ "full_receiving_address" ] == "hs1qmockaddress123", "Address mismatch"
        print ( "Test passed: Wallet and node info retrieved" )


    def test_find_soonest_expiring_name ():
        print ( "Testing find_soonest_expiring_name..." )
        mock_data = {
            "test1.hns": { "expiration_date": (datetime.now () + timedelta ( days=10 )).isoformat () },
            "test2.hns": { "expiration_date": (datetime.now () + timedelta ( days=5 )).isoformat () }
        }
        with open ( NAMES_JSON_FILE, 'w' ) as f:
            json.dump ( mock_data, f )
        result = find_soonest_expiring_name ()
        assert result [ "name" ] == "test2.hns", "Wrong soonest expiring name"
        assert 4 <= result [ "days_until_expire" ] <= 5, "Days until expire mismatch"
        print ( "Test passed: Soonest expiring name found" )


    # Run all tests
    print ( "Running utils.py tests..." )
    test_check_wallet_existing ()
    test_fetch_and_save_names ()
    test_renew_names ()
    test_get_wallet_and_node_info ()
    test_find_soonest_expiring_name ()
    print ( "All tests completed!" )