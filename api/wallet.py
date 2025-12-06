import json
import logging
import os
from typing import Dict, Optional, List, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from config.json
CONFIG_FILE = 'config.json'
if not os.path.exists(CONFIG_FILE):
    logger.error(f"Configuration file {CONFIG_FILE} not found")
    raise FileNotFoundError(f"Configuration file {CONFIG_FILE} not found")

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

class WALLET:
    """A client for interacting with the Handshake wallet API."""

    def __init__(self, api_key: Optional[str] = None, ip_address: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize the Wallet client with optional parameters, falling back to config.json values.

        Args:
            api_key (str, optional): Wallet API key. Defaults to WALLET_API from config.json.
            ip_address (str, optional): Wallet node IP address. Defaults to WALLET_ADDRESS from config.json.
            port (int, optional): Wallet node port. Defaults to WALLET_PORT from config.json.

        Raises:
            ValueError: If required configuration (api_key) is missing.
        """
        self.api_key = api_key or config.get('WALLET_API')
        self.address = ip_address or config.get('WALLET_ADDRESS', '127.0.0.1')
        self.port = port if port is not None else config.get('WALLET_PORT', 12039)

        if not self.api_key:
            logger.error("WALLET_API key is required but not found in config.json or provided as argument")
            raise ValueError("WALLET_API key is required. Set it in config.json or pass it as an argument.")

        self.base_url = f'http://x:{self.api_key}@{self.address}:{self.port}'

        # Configure requests session with retries and timeouts
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)

        logger.debug(f"Initialized WALLET client with base URL: {self.base_url}")

    def __enter__(self):
        """Support context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the session when exiting context."""
        self.session.close()
        logger.debug("WALLET session closed")

    def get_wallet_info(self, wallet_id: str) -> Dict[str, Any]:
        """
        Fetch information about a specific wallet.

        Args:
            wallet_id (str): The ID of the wallet to query.

        Returns:
            Dict[str, Any]: Wallet information (e.g., ID, balance).

        Raises:
            requests.RequestException: If the API call fails after retries.
        """
        url = f"{self.base_url}/wallets/{wallet_id}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched wallet info for {wallet_id}")
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch wallet info for {wallet_id}: {str(e)}")
            raise

    def __enter__(self):
        """Support context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the session when exiting context."""
        self.session.close()
        logger.debug("WALLET session closed")

    def _make_request(self, method: str, endpoint: str, data: str = '') -> Dict[str, Any]:
        """
        Make an HTTP request to the wallet API.

        Args:
            method (str): HTTP method (get, post, put, delete)
            endpoint (str): API endpoint
            data (str, optional): Request body data

        Returns:
            Dict[str, Any]: JSON response or error dictionary
        """
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.request(method, url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    # Core HTTP methods
    def get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the API."""
        return self._make_request('get', endpoint)

    def post(self, endpoint: str, message: str = '') -> Dict[str, Any]:
        """Make a POST request to the API."""
        return self._make_request('post', endpoint, message)

    def put(self, endpoint: str, message: str = '') -> Dict[str, Any]:
        """Make a PUT request to the API."""
        return self._make_request('put', endpoint, message)

    def delete(self, endpoint: str, message: str = '') -> Dict[str, Any]:
        """Make a DELETE request to the API."""
        return self._make_request('delete', endpoint, message)

    # Wallet Management Methods
    def create_wallet( self, passphrase: str, id: str = 'primary', account_key: str = '',
                       type: str = 'pubkeyhash', mnemonic: str = '', master: str = '',
                       watch_only: bool = True, m: int = 1, n: int = 1 ) -> Dict[str, Any]:
        """Create a new wallet with specified parameters."""
        endpoint = f'/wallet/{id}'
        payload = {
            "passphrase": passphrase,
            "_watch_only": '1' if watch_only else '0',
            "accountKey": account_key,
            "type": type,
            "master": master,
            "m": m,
            "n": n,
            "mnemonic": mnemonic
        }
        return self.put(endpoint, json.dumps(payload))

    def rescan ( self, height: int ) -> Dict [ str, Any ]:
        """Rescan the blockchain from a specific height."""
        endpoint = f'/rescan'
        payload = { "height": height }
        return self.post ( endpoint, json.dumps ( payload ) )

    def reset_auth_token(self, passphrase: str, id: str = 'primary') -> Dict[str, Any]:
        """Reset the authentication token for a wallet."""
        endpoint = f'/wallet/{id}/retoken'
        payload = {"passphrase": passphrase}
        return self.post(endpoint, json.dumps(payload))

    def get_wallet_info(self, id: str = '') -> Dict[str, Any]:
        """Get information about a specific wallet."""
        endpoint = f'/wallet/{id}'
        return self.get(endpoint)

    def get_master_hd_key(self, id: str = 'primary') -> Dict[str, Any]:
        """Get the master HD key for a wallet."""
        endpoint = f'/wallet/{id}/master'
        return self.get(endpoint)

    def change_password(self, new_passphrase: str, id: str = 'primary',
                        old_passphrase: str = '') -> Dict[str, Any]:
        """Change the wallet's passphrase."""
        endpoint = f'/wallet/{id}/passphrase'
        payload = {"old": old_passphrase, "passphrase": new_passphrase}
        return self.post(endpoint, json.dumps(payload))

    def lock_wallet(self, id: str = 'primary') -> Dict[str, Any]:
        """Lock a wallet."""
        endpoint = f'/wallet/{id}/lock'
        return self.post(endpoint)

    def unlock_wallet(self, passphrase: str, timeout: int = 0, id: str = 'primary') -> Dict[str, Any]:
        """Unlock a wallet."""
        endpoint = f'/wallet/{id}/unlock'
        payload = {"passphrase": passphrase, "timeout": timeout}
        return self.post(endpoint, json.dumps(payload))

    def list_wallets(self) -> Dict[str, Any]:
        """List all wallet IDs."""
        endpoint = '/wallet/'
        return self.get(endpoint)

    # Account Management Methods
    def get_wallet_account_list(self, id: str = 'primary') -> Dict[str, Any]:
        """List all account names for a wallet."""
        endpoint = f'/wallet/{id}/account'
        return self.get(endpoint)

    def get_account_info(self, id: str = 'primary', account: str = 'default') -> Dict[str, Any]:
        """Get account info."""
        endpoint = f'/wallet/{id}/account/{account}'
        return self.get(endpoint)

    def create_account(self, passphrase: str, id: str, account: str, account_key: str = '',
                       type: str = 'pubkeyhash', m: int = 1, n: int = 1) -> Dict[str, Any]:
        """Create an account with specified parameters."""
        endpoint = f'/wallet/{id}/account/{account}'
        payload = {
            "type": type,
            "passphrase": passphrase,
            "accountKey": account_key,
            "m": m,
            "n": n
        }
        return self.put(endpoint, json.dumps(payload))

    def generate_receiving_address(self, account: str, id: str = 'primary') -> Dict[str, Any]:
        """Derive new receiving address for account."""
        endpoint = f'/wallet/{id}/address'
        payload = {"account": account}
        return self.post(endpoint, json.dumps(payload))

    def generate_change_address(self, account: str = 'default', id: str = 'primary') -> Dict[str, Any]:
        """Derive new change address for account."""
        endpoint = f'/wallet/{id}/change'
        payload = {"account": account}
        return self.post(endpoint, json.dumps(payload))

    def get_balance(self, account: str = '', id: str = 'primary') -> Dict[str, Any]:
        """Get wallet or account balance."""
        endpoint = f'/wallet/{id}/balance?account={account}'
        return self.get(endpoint)

    # Key Management Methods
    def import_public_key(self, account: str, public_key: str, id: str = 'primary') -> Dict[str, Any]:
        """Import a public key."""
        endpoint = f'/wallet/{id}/import'
        payload = {"account": account, "publicKey": public_key}
        return self.post(endpoint, json.dumps(payload))

    def import_private_key(self, account: str, private_key: str, id: str = 'primary') -> Dict[str, Any]:
        """Import a private key."""
        endpoint = f'/wallet/{id}/import'
        payload = {"account": account, "privateKey": private_key}
        return self.post(endpoint, json.dumps(payload))

    def import_address(self, account: str, address: str, id: str = 'primary') -> Dict[str, Any]:
        """Import a Bech32 encoded address."""
        endpoint = f'/wallet/{id}/import'
        payload = {"account": account, "address": address}
        return self.post(endpoint, json.dumps(payload))

    def get_public_key_by_address(self, address: str, id: str = 'primary') -> Dict[str, Any]:
        """Get wallet key by address."""
        endpoint = f'/wallet/{id}/key/{address}'
        return self.get(endpoint)

    def get_private_key_by_address(self, address: str, passphrase: str, id: str = 'primary') -> Dict[str, Any]:
        """Get wallet private key by address."""
        endpoint = f'/wallet/{id}/wif/{address}?passphrase={passphrase}'
        return self.get(endpoint)

    def add_xpub_key(self, account_key: str, account: str = 'default', id: str = 'primary') -> Dict[str, Any]:
        """Add a shared xpubkey to a multisig wallet."""
        endpoint = f'/wallet/{id}/shared-key'
        payload = {"accountKey": account_key, "account": account}
        return self.put(endpoint, json.dumps(payload))

    def remove_xpub_key(self, account_key: str, account: str = 'default', id: str = 'primary') -> Dict[str, Any]:
        """Remove a shared xpubkey from a multisig wallet."""
        endpoint = f'/wallet/{id}/shared-key'
        payload = {"accountKey": account_key, "account": account}
        return self.delete(endpoint, json.dumps(payload))

    # Transaction Methods
    def sign_transaction(self, passphrase: str, tx_hex: str, id: str = 'primary') -> Dict[str, Any]:
        """Sign a transaction."""
        endpoint = f'/wallet/{id}/sign'
        payload = {"tx": tx_hex, "passphrase": passphrase}
        return self.post(endpoint, json.dumps(payload))

    def send_transaction(self, id: str, passphrase: str, rate: int, value: Optional[float] = None,
                         smart: bool = False, blocks: Optional[int] = None, max_fee: Optional[int] = None,
                         subtract_fee: bool = False, subtract_index: Optional[int] = None,
                         selection: str = 'all', depth: Optional[int] = None,
                         address: str = '') -> Dict[str, Any]:
        """Create, sign, and send a transaction."""
        endpoint = f'/wallet/{id}/send'
        outputs = [{
            "address": address,
            "value": value,
            "smart": '1' if smart else '0',
            "blocks": blocks,
            "maxFee": max_fee,
            "_subtract_fee": '1' if subtract_fee else '0',
            "subtractIndex": subtract_index,
            "selection": selection,
            "depth": depth
        }]
        payload = {
            "passphrase": passphrase,
            "rate": rate,
            "outputs": [o for o in outputs if o["value"] is not None]
        }
        return self.post(endpoint, json.dumps(payload))

    def create_transaction(self, id: str, passphrase: str, rate: int, value: Optional[float] = None,
                           smart: bool = False, blocks: Optional[int] = None, max_fee: Optional[int] = None,
                           subtract_fee: bool = False, subtract_index: Optional[int] = None,
                           selection: str = 'all', depth: Optional[int] = None,
                           address: str = '') -> Dict[str, Any]:
        """Create and template a transaction without broadcasting."""
        endpoint = f'/wallet/{id}/create'
        outputs = [{
            "address": address,
            "value": value,
            "smart": '1' if smart else '0',
            "blocks": blocks,
            "maxFee": max_fee,
            "_subtract_fee": '1' if subtract_fee else '0',
            "subtractIndex": subtract_index,
            "selection": selection,
            "depth": depth
        }]
        payload = {
            "passphrase": passphrase,
            "rate": rate,
            "outputs": [o for o in outputs if o["value"] is not None]
        }
        return self.post(endpoint, json.dumps(payload))

    def zap_transactions(self, account: str, id: str = 'primary', age: int = 0) -> Dict[str, Any]:
        """Remove pending transactions older than specified age."""
        endpoint = f'/wallet/{id}/zap'
        payload = {"account": account, "age": age}
        return self.post(endpoint, json.dumps(payload))

    def get_wallet_tx_details(self, id: str = 'primary', tx_hash: str = '') -> Dict[str, Any]:
        """Get wallet transaction details."""
        endpoint = f'/wallet/{id}/tx/{tx_hash}'
        return self.get(endpoint)

    def delete_transaction(self, id: str = 'primary', tx_hash: str = '') -> Dict[str, Any]:
        """Abandon a single pending transaction."""
        endpoint = f'/wallet/{id}/tx/{tx_hash}'
        return self.delete(endpoint)

    def get_wallet_tx_history(self, id: str = 'primary') -> Dict[str, Any]:
        """Get wallet transaction history."""
        endpoint = f'/wallet/{id}/tx/history'
        return self.get(endpoint)

    def get_pending_transactions(self, id: str = 'primary') -> Dict[str, Any]:
        """Get pending wallet transactions."""
        endpoint = f'/wallet/{id}/tx/unconfirmed'
        return self.get(endpoint)

    def get_range_of_transactions(self, start: int = 0, end: int = 0, id: str = 'primary') -> Dict[str, Any]:
        """Get range of wallet transactions by timestamp."""
        endpoint = f'/wallet/{id}/tx/range?start={start}&end={end}'
        return self.get(endpoint)

    def get_blocks_with_wallet_tx(self, id: str = 'primary') -> Dict[str, Any]:
        """List block heights containing wallet transactions."""
        endpoint = f'/wallet/{id}/block'
        return self.get(endpoint)

    def get_wallet_block_by_height(self, height: int, id: str = 'primary') -> Dict[str, Any]:
        """Get block info by height."""
        endpoint = f'/wallet/{id}/block/{height}'
        return self.get(endpoint)

    # Coin Management Methods
    def list_coins(self, id: str = 'primary') -> Dict[str, Any]:
        """List all wallet coins."""
        endpoint = f'/wallet/{id}/coin'
        return self.get(endpoint)

    def get_wallet_coin(self, tx_hash: str, index: str = '0', id: str = 'primary') -> Dict[str, Any]:
        """Get wallet coin."""
        endpoint = f'/wallet/{id}/coin/{tx_hash}/{index}'
        return self.get(endpoint)

    def lock_coin_outpoints(self, tx_hash: str, index: str = '0', id: str = 'primary') -> Dict[str, Any]:
        """Lock coin outpoints."""
        endpoint = f'/wallet/{id}/locked/{tx_hash}/{index}'
        return self.put(endpoint)

    def unlock_coin_outpoints(self, tx_hash: str, index: str = '0', id: str = 'primary') -> Dict[str, Any]:
        """Unlock coin outpoints."""
        endpoint = f'/wallet/{id}/locked/{tx_hash}/{index}'
        return self.delete(endpoint)

    def get_locked_outpoints(self, id: str = 'primary') -> Dict[str, Any]:
        """Get all locked outpoints."""
        endpoint = f'/wallet/{id}/locked'
        return self.get(endpoint)

    # Name and Auction Methods
    def get_wallet_names(self, id: str = 'primary') -> Dict[str, Any]:
        """List states of all names known to the wallet."""
        endpoint = f'/wallet/{id}/name'
        return self.get(endpoint)

    def get_wallet_names_own(self, id: str = 'primary') -> Dict[str, Any]:
        """List all names belong to the wallet."""
        endpoint = f'/wallet/{id}/name?own=true'
        return self.get(endpoint)

    def get_wallet_name(self, name: str = '', id: str = 'primary') -> Dict[str, Any]:
        """List status of a single name."""
        endpoint = f'/wallet/{id}/name/{name}'
        return self.get(endpoint)

    def get_wallet_auctions(self, id: str = 'primary') -> Dict[str, Any]:
        """List states of all auctions known to the wallet."""
        endpoint = f'/wallet/{id}/auction'
        return self.get(endpoint)

    def get_wallet_auction_by_name ( self, name: str = '', id: str = 'primary' ) -> Dict [ str, Any ]:
        """Get auction state by name."""
        endpoint = f'/wallet/{id}/auction/{name}'
        return self.get ( endpoint )

    def get_wallet_bids ( self, id: str = 'primary', own: bool = True ) -> Dict [ str, Any ]:
        """List all bids for all names."""
        endpoint = f'/wallet/{id}/bid?own={"1" if own else "0"}'
        return self.get ( endpoint )

    def get_wallet_bids_by_name ( self, name: str = '', id: str = 'primary', own: bool = False ) -> Dict [ str, Any ]:
        """List bids for a specific name."""
        endpoint = f'/wallet/{id}/bid/{name}?own={"1" if own else "0"}'
        return self.get ( endpoint )

    def get_wallet_reveals ( self, id: str = 'primary', own: bool = False ) -> Dict [ str, Any ]:
        """List all reveals for all names."""
        endpoint = f'/wallet/{id}/reveal?own={"1" if own else "0"}'
        return self.get ( endpoint )

    def get_wallet_reveals_by_name ( self, name: str, id: str = 'primary', own: bool = False ) -> Dict [ str, Any ]:
        """List reveals for a specific name."""
        endpoint = f'/wallet/{id}/reveal/{name}?own={"1" if own else "0"}'
        return self.get ( endpoint )

    def get_wallet_resource_by_name ( self, name: str, id: str = 'primary' ) -> Dict [ str, Any ]:
        """Get data resource associated with a name."""
        endpoint = f'/wallet/{id}/resource/{name}'
        return self.get ( endpoint )

    def get_nonce_for_bid ( self, bid: float, name: str, address: str, id: str = 'primary' ) -> Dict [ str, Any ]:
        """Generate a nonce to blind a bid."""
        endpoint = f'/wallet/{id}/nonce/{name}?address={address}&bid={bid}'
        return self.get ( endpoint )

    def send_open ( self, id: str = '', passphrase: str = '', name: str = '',
                    sign: bool = True, broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a name OPEN."""
        endpoint = f'/wallet/{id}/open'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0'
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_bid ( self, id: str, passphrase: str, name: str, bid: int, lockup: int,
                   sign: bool = True, broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a name BID."""
        endpoint = f'/wallet/{id}/bid'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0',
            "bid": bid,
            "lockup": lockup
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_reveal ( self, id: str, passphrase: str, name: str = '', sign: bool = True,
                      broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a name REVEAL."""
        endpoint = f'/wallet/{id}/reveal'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0'
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_redeem ( self, id: str, passphrase: str, name: str = '', sign: bool = True,
                      broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a REDEEM."""
        endpoint = f'/wallet/{id}/redeem'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0'
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_update ( self, id: str, passphrase: str, name: str, data: str, sign: bool = True,
                      broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send an UPDATE."""
        endpoint = f'/wallet/{id}/update'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0',
            "data": data
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    # def send_renew ( self, id: str, passphrase: str, name: str, sign: bool = True,
    #                  broadcast: bool = True ) -> Dict [ str, Any ]:
    #     """Create, sign, and send a RENEW."""
    #     endpoint = f'/wallet/{id}/renewal'
    #     payload = {
    #         "passphrase": passphrase,
    #         "name": name,
    #         "broadcast": '1' if broadcast else '0',
    #         "sign": '1' if sign else '0'
    #     }
    #     return self.post ( endpoint, json.dumps ( payload ) )

    def send_renew ( self, id: str, passphrase: str, name: str, sign: bool = True,
                     broadcast: bool = True    ) -> Dict [ str, Any ]:
        """Create, sign, and send a RENEW."""
        endpoint = f'/wallet/{id}/renewal'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": 1 if broadcast else 0,  # better: send real bool/int
            "sign": 1 if sign else 0
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_transfer ( self, id: str, passphrase: str, name: str, address: str, sign: bool = True,
                        broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a TRANSFER."""
        endpoint = f'/wallet/{id}/transfer'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0',
            "address": address
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def cancel_transfer ( self, id: str, passphrase: str, name: str, sign: bool = True,
                          broadcast: bool = True ) -> Dict [ str, Any ]:
        """Cancel a TRANSFER."""
        endpoint = f'/wallet/{id}/cancel'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0'
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_finalize ( self, id: str, passphrase: str, name: str, sign: bool = True,
                        broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a FINALIZE."""
        endpoint = f'/wallet/{id}/finalize'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0'
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    def send_revoke ( self, id: str, passphrase: str, name: str, sign: bool = True,
                      broadcast: bool = True ) -> Dict [ str, Any ]:
        """Create, sign, and send a REVOKE."""
        endpoint = f'/wallet/{id}/revoke'
        payload = {
            "passphrase": passphrase,
            "name": name,
            "broadcast": '1' if broadcast else '0',
            "sign": '1' if sign else '0'
        }
        return self.post ( endpoint, json.dumps ( payload ) )

    # RPC Methods (continued from here)
    def rpc_get_bids ( self ) -> Dict [ str, Any ]:
        """Get list of BIDs placed by the wallet."""
        endpoint = '/'
        payload = { "method": "getbids", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_reveals ( self ) -> Dict [ str, Any ]:
        """Get all REVEAL transactions sent by the wallet."""
        endpoint = '/'
        payload = { "method": "getreveals", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_open ( self, name: str ) -> Dict [ str, Any ]:
        """Send an OPEN transaction."""
        endpoint = '/'
        payload = { "method": "sendopen", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_bid ( self, name: str, bid_amount: float, lockup_blind: float,
                       account: str = 'default' ) -> Dict [ str, Any ]:
        """Send a BID transaction."""
        endpoint = '/'
        payload = { "method": "sendbid", "params": [ name, bid_amount, lockup_blind, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_reveal ( self, name: str = '' ) -> Dict [ str, Any ]:
        """Send a REVEAL transaction."""
        endpoint = '/'
        payload = { "method": "sendreveal", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_redeem ( self, name: str = '' ) -> Dict [ str, Any ]:
        """Send a REDEEM transaction."""
        endpoint = '/'
        payload = { "method": "sendredeem", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_update ( self, name: str, data: Dict [ str, Any ] ) -> Dict [ str, Any ]:
        """Send an UPDATE transaction."""
        endpoint = '/'
        payload = { "method": "sendupdate", "params": [ name, data ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_renewal ( self, name: str ) -> Dict [ str, Any ]:
        """Send a RENEWAL transaction."""
        endpoint = '/'
        payload = { "method": "sendrenewal", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_transfer ( self, name: str, address: str ) -> Dict [ str, Any ]:
        """Send a TRANSFER transaction."""
        endpoint = '/'
        payload = { "method": "sendtransfer", "params": [ name, address ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_finalize ( self, name: str ) -> Dict [ str, Any ]:
        """Send a FINALIZE transaction."""
        endpoint = '/'
        payload = { "method": "sendfinalize", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_cancel ( self, name: str ) -> Dict [ str, Any ]:
        """Send a CANCEL transaction."""
        endpoint = '/'
        payload = { "method": "sendcancel", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_revoke ( self, name: str ) -> Dict [ str, Any ]:
        """Send a REVOKE transaction."""
        endpoint = '/'
        payload = { "method": "sendrevoke", "params": [ name ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_nonce ( self, name: str, address: str, bid_value: float ) -> Dict [ str, Any ]:
        """Regenerate nonce for a bid."""
        endpoint = '/'
        payload = { "method": "importnonce", "params": [ name, address, bid_value ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_open ( self, name: str, force: bool, account: str ) -> Dict [ str, Any ]:
        """Create an OPEN transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createopen", "params": [ name, '1' if force else '0', account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_bid ( self, name: str, bid_amount: float, lockup_blind: float,
                         account: str ) -> Dict [ str, Any ]:
        """Create a BID transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createbid", "params": [ name, bid_amount, lockup_blind, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_reveal ( self, name: str = '', account: str = '' ) -> Dict [ str, Any ]:
        """Create a REVEAL transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createreveal", "params": [ name, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_redeem ( self, name: str = '', account: str = '' ) -> Dict [ str, Any ]:
        """Create a REDEEM transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createredeem", "params": [ name, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_update ( self, name: str, data: Dict [ str, Any ], account: str = '' ) -> Dict [ str, Any ]:
        """Create an UPDATE transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createupdate", "params": [ name, data, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_renewal ( self, name: str, account: str = '' ) -> Dict [ str, Any ]:
        """Create a RENEWAL transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createrenewal", "params": [ name, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_transfer ( self, name: str, address: str, account: str = '' ) -> Dict [ str, Any ]:
        """Create a TRANSFER transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createtransfer", "params": [ name, address, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_finalize ( self, name: str, account: str = '' ) -> Dict [ str, Any ]:
        """Create a FINALIZE transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createfinalize", "params": [ name, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_cancel ( self, name: str, account: str = '' ) -> Dict [ str, Any ]:
        """Create a CANCEL transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createcancel", "params": [ name, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_revoke ( self, name: str, account: str = '' ) -> Dict [ str, Any ]:
        """Create a REVOKE transaction without broadcasting."""
        endpoint = '/'
        payload = { "method": "createrevoke", "params": [ name, account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_name ( self, name: str, rescan_height: Optional [ int ] = None ) -> Dict [ str, Any ]:
        """Add a name to the wallet watchlist."""
        endpoint = '/'
        params = [ name ] if rescan_height is None else [ name, rescan_height ]
        payload = { "method": "importname", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_select_wallet ( self, wallet_id: str ) -> Dict [ str, Any ]:
        """Switch target wallet for RPC calls."""
        endpoint = '/'
        payload = { "method": "selectwallet", "params": [ wallet_id ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_wallet_info ( self ) -> Dict [ str, Any ]:
        """Get basic wallet details."""
        endpoint = '/'
        payload = { "method": "getwalletinfo", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_fund_raw_transaction ( self, tx_hex: str, fee_rate: Optional [ float ] = None,
                                   change_address: Optional [ str ] = None ) -> Dict [ str, Any ]:
        """Add inputs to a transaction."""
        endpoint = '/'
        options = { }
        if fee_rate is not None:
            options [ 'feeRate' ] = fee_rate
        if change_address is not None:
            options [ 'changeAddress' ] = change_address
        params = [ tx_hex ] if not options else [ tx_hex, options ]
        payload = { "method": "fundrawtransaction", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_resend_wallet_transactions ( self ) -> Dict [ str, Any ]:
        """Re-broadcast all unconfirmed transactions."""
        endpoint = '/'
        payload = { "method": "resendwallettransactions", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_abandon_transaction ( self, tx_id: str ) -> Dict [ str, Any ]:
        """Remove transaction from the database."""
        endpoint = '/'
        payload = { "method": "abandontransaction", "params": [ tx_id ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_backup_wallet ( self, path: str ) -> Dict [ str, Any ]:
        """Backup wallet database."""
        endpoint = '/'
        payload = { "method": "backupwallet", "params": [ path ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_dump_priv_key ( self, address: str ) -> Dict [ str, Any ]:
        """Get private key for an address."""
        endpoint = '/'
        payload = { "method": "dumpprivkey", "params": [ address ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_dump_wallet ( self, path: str ) -> Dict [ str, Any ]:
        """Dump wallet private keys to a file."""
        endpoint = '/'
        payload = { "method": "dumpwallet", "params": [ path ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_encrypt_wallet ( self, passphrase: str ) -> Dict [ str, Any ]:
        """Encrypt the wallet."""
        endpoint = '/'
        payload = { "method": "encryptwallet", "params": [ passphrase ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_account_address ( self, account: str = 'default' ) -> Dict [ str, Any ]:
        """Get current receiving address for an account."""
        endpoint = '/'
        payload = { "method": "getaccountaddress", "params": [ account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_account ( self, address: str ) -> Dict [ str, Any ]:
        """Get account associated with an address."""
        endpoint = '/'
        payload = { "method": "getaccount", "params": [ address ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_addresses_by_account ( self, account: str = 'default' ) -> Dict [ str, Any ]:
        """Get all addresses for an account."""
        endpoint = '/'
        payload = { "method": "getaddressesbyaccount", "params": [ account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_balance ( self, account: Optional [ str ] = None ) -> Dict [ str, Any ]:
        """Get total balance for wallet or account."""
        endpoint = '/'
        params = [ account ] if account is not None else [ ]
        payload = { "method": "getbalance", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_new_address ( self, account: str = '' ) -> Dict [ str, Any ]:
        """Get next receiving address."""
        endpoint = '/'
        payload = { "method": "getnewaddress", "params": [ account ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_raw_change_address ( self ) -> Dict [ str, Any ]:
        """Get next change address."""
        endpoint = '/'
        payload = { "method": "getrawchangeaddress", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_received_by_account ( self, account: str, min_confirm: Optional [ int ] = None ) -> Dict [ str, Any ]:
        """Get total amount received by account."""
        endpoint = '/'
        params = [ account ] if min_confirm is None else [ account, min_confirm ]
        payload = { "method": "getreceivedbyaccount", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_received_by_address ( self, address: str, min_confirm: Optional [ int ] = None ) -> Dict [ str, Any ]:
        """Get total amount received by address."""
        endpoint = '/'
        params = [ address ] if min_confirm is None else [ address, min_confirm ]
        payload = { "method": "getreceivedbyaddress", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_transaction ( self, tx_id: str, watch_only: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Get transaction details."""
        endpoint = '/'
        params = [ tx_id ] if watch_only is None else [ tx_id, '1' if watch_only else '0' ]
        payload = { "method": "gettransaction", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_unconfirmed_balance ( self ) -> Dict [ str, Any ]:
        """Get unconfirmed balance."""
        endpoint = '/'
        payload = { "method": "getunconfirmedbalance", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_priv_key ( self, private_key: str, label: Optional [ str ] = None,
                              rescan: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Import a private key."""
        endpoint = '/'
        params = [ private_key ]
        if label is not None or rescan is not None:
            params.append ( label if label is not None else '' )
            if rescan is not None:
                params.append ( '1' if rescan else '0' )
        payload = { "method": "importprivkey", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_wallet ( self, wallet_file: str, rescan: bool = False ) -> Dict [ str, Any ]:
        """Import keys from a wallet file."""
        endpoint = '/'
        payload = { "method": "importwallet", "params": [ wallet_file, '1' if rescan else '0' ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_address ( self, address: str, label: Optional [ str ] = None,
                             rescan: Optional [ bool ] = None, p2sh: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Import an address to a watch-only wallet."""
        endpoint = '/'
        params = [ address ]
        if label is not None or rescan is not None or p2sh is not None:
            params.append ( label if label is not None else '' )
            params.append ( '1' if rescan else '0' ) if rescan is not None else params.append ( '0' )
            params.append ( '1' if p2sh else '0' ) if p2sh is not None else None
        payload = { "method": "importaddress", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_pruned_funds ( self, tx_hex: str, tx_out_proof: str ) -> Dict [ str, Any ]:
        """Import funds into pruned wallets."""
        endpoint = '/'
        payload = { "method": "importprunedfunds", "params": [ tx_hex, tx_out_proof ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_import_pub_key ( self, public_hex_key: str, label: Optional [ str ] = None,
                             rescan: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Import a public key."""
        endpoint = '/'
        params = [ public_hex_key ]
        if label is not None or rescan is not None:
            params.append ( label if label is not None else '' )
            if rescan is not None:
                params.append ( '1' if rescan else '0' )
        payload = { "method": "importpubkey", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_accounts ( self, min_confirm: Optional [ int ] = None,
                            watch_only: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Get list of account names and balances."""
        endpoint = '/'
        params = [ ]
        if min_confirm is not None or watch_only is not None:
            params.append ( min_confirm if min_confirm is not None else 1 )
            params.append ( '1' if watch_only else '0' ) if watch_only is not None else None
        payload = { "method": "listaccounts", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_lock_unspent ( self, lock: bool = True, outputs: Optional [ List [ Dict [ str, Any ] ] ] = None ) -> Dict [
        str, Any ]:
        """Lock or unlock transaction outputs."""
        endpoint = '/'
        params = [ '1' if lock else '0' ]
        if outputs is not None:
            params.append ( outputs )
        payload = { "method": "lockunspent", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_lock_unspent ( self ) -> Dict [ str, Any ]:
        """Get list of locked outputs."""
        endpoint = '/'
        payload = { "method": "listlockunspent", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_received_by_account ( self, min_confirm: Optional [ int ] = None,
                                       include_empty: Optional [ bool ] = None,
                                       watch_only: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Get balances for all accounts."""
        endpoint = '/'
        params = [ ]
        if min_confirm is not None or include_empty is not None or watch_only is not None:
            params.append ( min_confirm if min_confirm is not None else 1 )
            params.append ( '1' if include_empty else '0' ) if include_empty is not None else params.append ( '0' )
            params.append ( '1' if watch_only else '0' ) if watch_only is not None else params.append ( '0' )
        payload = { "method": "listreceivedbyaccount", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_received_by_address ( self, min_confirm: Optional [ int ] = None,
                                       include_empty: Optional [ bool ] = None,
                                       watch_only: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Get balances for all addresses."""
        endpoint = '/'
        params = [ ]
        if min_confirm is not None or include_empty is not None or watch_only is not None:
            params.append ( min_confirm if min_confirm is not None else 1 )
            params.append ( '1' if include_empty else '0' ) if include_empty is not None else params.append ( '0' )
            params.append ( '1' if watch_only else '0' ) if watch_only is not None else params.append ( '0' )
        payload = { "method": "listreceivedbyaddress", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_since_block ( self, block_hash: Optional [ str ] = None,
                               min_confirm: Optional [ int ] = None,
                               watch_only: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Get transactions since a block."""
        endpoint = '/'
        params = [ ]
        if block_hash is not None or min_confirm is not None or watch_only is not None:
            params.append ( block_hash if block_hash is not None else '' )
            params.append ( min_confirm if min_confirm is not None else 1 )
            params.append ( '1' if watch_only else '0' ) if watch_only is not None else params.append ( '0' )
        payload = { "method": "listsinceblock", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_transactions ( self, account: str = '*', count: int = 10, skip: int = 0,
                                watch_only: Optional [ bool ] = None ) -> Dict [ str, Any ]:
        """Get recent transactions."""
        endpoint = '/'
        params = [ account, count, skip ]
        if watch_only is not None:
            params.append ( '1' if watch_only else '0' )
        payload = { "method": "listtransactions", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_list_unspent ( self, min_confirm: Optional [ int ] = None, max_confirm: Optional [ int ] = None,
                           addresses: Optional [ List [ str ] ] = None ) -> Dict [ str, Any ]:
        """Get unspent transaction outputs."""
        endpoint = '/'
        params = [ ]
        if min_confirm is not None or max_confirm is not None or addresses is not None:
            params.append ( min_confirm if min_confirm is not None else 0 )
            params.append ( max_confirm if max_confirm is not None else 9999999 )
            params.append ( addresses if addresses is not None else [ ] )
        payload = { "method": "listunspent", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_from ( self, from_account: str, to_address: str, amount: float,
                        min_confirm: Optional [ int ] = None ) -> Dict [ str, Any ]:
        """Send HNS from an account to an address."""
        endpoint = '/'
        params = [ from_account, to_address, amount ]
        if min_confirm is not None:
            params.append ( min_confirm )
        payload = { "method": "sendfrom", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_many ( self, from_account: str, outputs: Dict [ str, float ], min_confirm: Optional [ int ] = None,
                        subtract_fee: Optional [ bool ] = None, label: Optional [ str ] = None ) -> Dict [ str, Any ]:
        """Send HNS to multiple addresses."""
        endpoint = '/'
        params = [ from_account, outputs ]
        if min_confirm is not None or subtract_fee is not None or label is not None:
            params.append ( min_confirm if min_confirm is not None else 1 )
            if subtract_fee is not None or label is not None:
                params.append ( label if label is not None else '' )
                params.append ( '1' if subtract_fee else '0' ) if subtract_fee is not None else None
        payload = { "method": "sendmany", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_create_send_to_address ( self, to_address: str, amount: float, subtract_fee: Optional [ bool ] = None,
                                     comment: Optional [ str ] = None, comment_to: Optional [ str ] = None ) -> Dict [
        str, Any ]:
        """Create a transaction without broadcasting."""
        endpoint = '/'
        params = [ to_address, amount ]
        if subtract_fee is not None or comment is not None or comment_to is not None:
            params.append ( comment if comment is not None else '' )
            params.append ( comment_to if comment_to is not None else '' )
            params.append ( '1' if subtract_fee else '0' ) if subtract_fee is not None else None
        payload = { "method": "createsendtoaddress", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_send_to_address ( self, to_address: str, amount: float, subtract_fee: Optional [ bool ] = None,
                              comment: Optional [ str ] = None, comment_to: Optional [ str ] = None ) -> Dict [
        str, Any ]:
        """Send HNS to an address."""
        endpoint = '/'
        params = [ to_address, amount ]
        if subtract_fee is not None or comment is not None or comment_to is not None:
            params.append ( comment if comment is not None else '' )
            params.append ( comment_to if comment_to is not None else '' )
            params.append ( '1' if subtract_fee else '0' ) if subtract_fee is not None else None
        payload = { "method": "sendtoaddress", "params": params }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_set_tx_fee ( self, tx_fee: float = 0 ) -> Dict [ str, Any ]:
        """Set the fee rate for transactions."""
        endpoint = '/'
        payload = { "method": "settxfee", "params": [ tx_fee ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_sign_message ( self, address: str, message: str ) -> Dict [ str, Any ]:
        """Sign a message with an address."""
        endpoint = '/'
        payload = { "method": "signmessage", "params": [ address, message ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_sign_message_with_name ( self, name: str, message: str ) -> Dict [ str, Any ]:
        """Sign a message with a name's address."""
        endpoint = '/'
        payload = { "method": "signmessagewithname", "params": [ name, message ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_wallet_lock ( self ) -> Dict [ str, Any ]:
        """Lock the wallet."""
        endpoint = '/'
        payload = { "method": "walletlock", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_wallet_password_change ( self, old_passphrase: str, new_passphrase: str ) -> Dict [ str, Any ]:
        """Change the wallet passphrase."""
        endpoint = '/'
        payload = { "method": "walletpassphrasechange", "params": [ old_passphrase, new_passphrase ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_wallet_passphrase ( self, passphrase: str, timeout: int = 600 ) -> Dict [ str, Any ]:
        """Unlock the wallet."""
        endpoint = '/'
        payload = { "method": "walletpassphrase", "params": [ passphrase, timeout ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_remove_pruned_funds ( self, tx_id: str ) -> Dict [ str, Any ]:
        """Remove pruned funds."""
        endpoint = '/'
        payload = { "method": "removeprunedfunds", "params": [ tx_id ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_get_memory_info ( self ) -> Dict [ str, Any ]:
        """Get memory usage information."""
        endpoint = '/'
        payload = { "method": "getmemoryinfo", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_set_log_level ( self, log_level: str = 'NONE' ) -> Dict [ str, Any ]:
        """Set the log level."""
        endpoint = '/'
        payload = { "method": "setloglevel", "params": [ log_level ] }
        return self.post ( endpoint, json.dumps ( payload ) )

    def rpc_stop ( self ) -> Dict [ str, Any ]:
        """Close the wallet database."""
        endpoint = '/'
        payload = { "method": "stop", "params": [ ] }
        return self.post ( endpoint, json.dumps ( payload ) )


if __name__ == "__main__":
    # Example usage
    try:
        wallet = WALLET ()

        # Test RPC get wallet info
        wallet_info = wallet.get_wallet_info ()
        print ( "RPC Wallet Info:", json.dumps ( wallet_info, indent=2 ) )

    except ValueError as e:
        print ( f"Initialization error: {e}" )
    except Exception as e:
        print ( f"Unexpected error: {e}" )
