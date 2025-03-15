#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from typing import Dict, Union, Optional, List
import json
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HSD:
    """A client for interacting with the Handshake (HSD) node REST and RPC API."""

    def __init__(self, api_key: Optional[str] = None, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize the HSD client with optional parameters, falling back to .env values.

        Args:
            api_key (str, optional): HSD API key. Defaults to NODE_API_KEY from .env.
            host (str, optional): HSD node host address. Defaults to NODE_HOST from .env.
            port (int, optional): HSD node port. Defaults to NODE_PORT from .env.

        Raises:
            ValueError: If required configuration (api_key) is missing.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("NODE_API_KEY")
        self.host = host or os.getenv("NODE_HOST", "127.0.0.1")
        self.port = port if port is not None else int(os.getenv("NODE_PORT", "12037"))

        if not self.api_key:
            logger.error("NODE_API_KEY is required but not found in .env or provided as argument")
            raise ValueError("NODE_API_KEY is required. Set it in .env or pass it as an argument.")

        self.base_url = f'http://x:{self.api_key}@{self.host}:{self.port}'
        self.session = requests.Session()
        logger.debug(f"Initialized HSD client with base URL: {self.base_url}")

    def _request(self, method: str, endpoint: str, data: Optional[str] = None) -> Dict[str, Union[str, dict]]:
        """Handle HTTP requests with improved error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = getattr(self.session, method)(url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"error": f"Failed to {method} {endpoint}: {str(e)}"}
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            return {"error": f"Invalid JSON response from {endpoint}"}

    def get(self, endpoint: str) -> Dict[str, Union[str, dict]]:
        """Send a GET request to the API."""
        return self._request('get', endpoint)

    def post(self, endpoint: str, message: str = '') -> Dict[str, Union[str, dict]]:
        """Send a POST request to the API."""
        return self._request('post', endpoint, message)

    def _rpc_post(self, method: str, params: Optional[List] = None) -> Dict[str, Union[str, dict]]:
        """Helper for RPC POST requests."""
        payload = {"method": method, "params": params or [], "id": "1"}
        return self.post('/', json.dumps(payload))

    # Existing REST API Methods
    def get_info(self) -> Dict[str, Union[str, dict]]:
        """Get server information."""
        return self.get('/')

    def get_mempool(self) -> Dict[str, Union[str, dict]]:
        """Get a snapshot of the mempool as an array of transaction JSONs."""
        return self.get('/mempool')

    def get_mempool_invalid(self, verbose: bool = False) -> Dict[str, Union[str, dict]]:
        """Get the mempool rejects filter (Bloom filter of rejected TX hashes)."""
        endpoint = '/mempool/invalid?verbose=true' if verbose else '/mempool/invalid'
        return self.get(endpoint)

    def get_mempool_invalid_hash(self, tx_hash: str) -> Dict[str, Union[str, dict]]:
        """Test a transaction hash against the mempool rejects filter."""
        return self.get(f'/mempool/invalid/{tx_hash}')

    def get_block_by_hash_or_height(self, block_hash_or_height: str) -> Dict[str, Union[str, dict]]:
        """Get block info by hash or height."""
        return self.get(f'/block/{block_hash_or_height}')

    def get_header_by_hash_or_height(self, header_hash_or_height: str) -> Dict[str, Union[str, dict]]:
        """Get block header by hash or height."""
        return self.get(f'/header/{header_hash_or_height}')

    def broadcast(self, tx_hex: str) -> Dict[str, Union[str, dict]]:
        """Broadcast a transaction to the node's mempool."""
        message = json.dumps({"tx": tx_hex})
        return self.post('/broadcast/', message)

    def broadcast_claim(self, claim: str) -> Dict[str, Union[str, dict]]:
        """Broadcast a claim to the node's mempool."""
        message = json.dumps({"claim": claim})
        return self.post('/claim/', message)

    def get_fee_estimate(self, blocks: int) -> Dict[str, Union[str, dict]]:
        """Estimate the fee required (in dollarydoos per kB) for confirmation."""
        return self.get(f'/fee?blocks={blocks}')

    # New REST API Methods
    def reset(self, height: int) -> Dict[str, Union[str, dict]]:
        """Trigger a hard-reset of the blockchain to a specific height."""
        message = json.dumps({"height": height})
        return self.post('/reset', message)

    def get_coin_by_hash_index(self, tx_hash: str, index: int) -> Dict[str, Union[str, dict]]:
        """Get coin by outpoint (hash and index) in HSD coin JSON format."""
        return self.get(f'/coin/{tx_hash}/{index}')

    def get_coin_by_address(self, address: str) -> Dict[str, Union[str, dict]]:
        """Get an array of coin objects by address."""
        return self.get(f'/coin/address/{address}')

    def get_tx_by_hash(self, tx_hash: str) -> Dict[str, Union[str, dict]]:
        """Get transaction objects array by hash."""
        return self.get(f'/tx/{tx_hash}')

    def get_tx_by_address(self, address: str) -> Dict[str, Union[str, dict]]:
        """Get transaction objects array by address."""
        return self.get(f'/tx/address/{address}')

    # New RPC Methods
    def rpc_stop(self) -> Dict[str, Union[str, dict]]:
        """Stop the running node."""
        return self._rpc_post("stop")

    def rpc_get_info(self) -> Dict[str, Union[str, dict]]:
        """Get general node information."""
        return self._rpc_post("getinfo")

    def rpc_get_memory_info(self) -> Dict[str, Union[str, dict]]:
        """Get memory usage information."""
        return self._rpc_post("getmemoryinfo")

    def rpc_set_log_level(self, log_level: str = 'NONE') -> Dict[str, Union[str, dict]]:
        """Change the log level of the running node (NONE, ERROR, WARNING, INFO, DEBUG, SPAM)."""
        return self._rpc_post("setloglevel", [log_level])

    def rpc_validate_address(self, address: str) -> Dict[str, Union[str, dict]]:
        """Validate an address."""
        return self._rpc_post("validateaddress", [address])

    def rpc_create_multisig(self, nrequired: int, keys: List[str]) -> Dict[str, Union[str, dict]]:
        """Create a multisig address."""
        return self._rpc_post("createmultisig", [nrequired, keys])

    def rpc_sign_message_with_privkey(self, private_key: str, message: str) -> Dict[str, Union[str, dict]]:
        """Sign a message with a private key."""
        return self._rpc_post("signmessagewithprivkey", [private_key, message])

    def rpc_verify_message(self, address: str, signature: str, message: str) -> Dict[str, Union[str, dict]]:
        """Verify a signature."""
        return self._rpc_post("verifymessage", [address, signature, message])

    def rpc_verify_message_with_name(self, name: str, signature: str, message: str) -> Dict[str, Union[str, dict]]:
        """Retrieve the address owning a name and verify its signature."""
        return self._rpc_post("verifymessagewithname", [name, signature, message])

    def rpc_set_mock_time(self, timestamp: int) -> Dict[str, Union[str, dict]]:
        """Change network time (consensus-critical)."""
        return self._rpc_post("setmocktime", [timestamp])

    def rpc_prune_blockchain(self) -> Dict[str, Union[str, dict]]:
        """Prune the blockchain, keeping blocks per network config."""
        return self._rpc_post("pruneblockchain")

    def rpc_invalidate_block(self, block_hash: str) -> Dict[str, Union[str, dict]]:
        """Invalidate a block in the chain."""
        return self._rpc_post("invalidateblock", [block_hash])

    def rpc_reconsider_block(self, block_hash: str) -> Dict[str, Union[str, dict]]:
        """Remove a block from the invalid block set."""
        return self._rpc_post("reconsiderblock", [block_hash])

    def rpc_get_blockchain_info(self) -> Dict[str, Union[str, dict]]:
        """Get blockchain information."""
        return self._rpc_post("getblockchaininfo")

    def rpc_get_best_block_hash(self) -> Dict[str, Union[str, dict]]:
        """Get the block hash of the chain tip."""
        return self._rpc_post("getbestblockhash")

    def rpc_get_block_count(self) -> Dict[str, Union[str, dict]]:
        """Get the current block count."""
        return self._rpc_post("getblockcount")

    def rpc_get_block(self, block_hash: str, verbose: bool = True, details: bool = False) -> Dict[str, Union[str, dict]]:
        """Get information about a block by hash."""
        return self._rpc_post("getblock", [block_hash, verbose, details])

    def rpc_get_block_by_height(self, block_height: int, verbose: bool = True, details: bool = False) -> Dict[str, Union[str, dict]]:
        """Get information about a block by height."""
        return self._rpc_post("getblockbyheight", [block_height, verbose, details])

    def rpc_get_block_hash(self, block_height: int) -> Dict[str, Union[str, dict]]:
        """Get a block's hash by its height."""
        return self._rpc_post("getblockhash", [block_height])

    def rpc_get_block_header(self, block_hash: str, verbose: bool = True) -> Dict[str, Union[str, dict]]:
        """Get a block's header by hash."""
        return self._rpc_post("getblockheader", [block_hash, verbose])

    def rpc_get_chain_tips(self) -> Dict[str, Union[str, dict]]:
        """Get chain tips."""
        return self._rpc_post("getchaintips")

    def rpc_get_difficulty(self) -> Dict[str, Union[str, dict]]:
        """Get the current difficulty level."""
        return self._rpc_post("getdifficulty")

    def rpc_get_mempool_info(self) -> Dict[str, Union[str, dict]]:
        """Get information about the mempool."""
        return self._rpc_post("getmempoolinfo")

    def rpc_get_mempool_ancestors(self, tx_hash: str, verbose: bool = False) -> Dict[str, Union[str, dict]]:
        """Get all in-mempool ancestors for a transaction."""
        return self._rpc_post("getmempoolancestors", [tx_hash, verbose])

    def rpc_get_mempool_descendants(self, tx_hash: str, verbose: bool = False) -> Dict[str, Union[str, dict]]:
        """Get all in-mempool descendants for a transaction."""
        return self._rpc_post("getmempooldescendants", [tx_hash, verbose])

    def rpc_get_mempool_entry(self, tx_hash: str) -> Dict[str, Union[str, dict]]:
        """Get mempool transaction info by hash."""
        return self._rpc_post("getmempoolentry", [tx_hash])

    def rpc_get_raw_mempool(self, verbose: bool = False) -> Dict[str, Union[str, dict]]:
        """Get detailed mempool information or transaction list."""
        return self._rpc_post("getrawmempool", [verbose])

    def rpc_prioritise_transaction(self, tx_hash: str, priority_delta: int, fee_delta: int) -> Dict[str, Union[str, dict]]:
        """Prioritize a transaction in the mempool."""
        return self._rpc_post("prioritisetransaction", [tx_hash, priority_delta, fee_delta])

    def rpc_estimate_fee(self, n_blocks: int = 1) -> Dict[str, Union[str, dict]]:
        """Estimate the fee for a transaction."""
        return self._rpc_post("estimatefee", [n_blocks])

    def rpc_estimate_priority(self, n_blocks: int = 1) -> Dict[str, Union[str, dict]]:
        """Estimate the priority needed for a free high-priority transaction."""
        return self._rpc_post("estimatepriority", [n_blocks])

    def rpc_estimate_smart_fee(self, n_blocks: int = 1) -> Dict[str, Union[str, dict]]:
        """Estimate a smart fee for a transaction."""
        return self._rpc_post("estimatesmartfee", [n_blocks])

    def rpc_estimate_smart_priority(self, n_blocks: int = 1) -> Dict[str, Union[str, dict]]:
        """Estimate a smart priority for a free high-priority transaction."""
        return self._rpc_post("estimatesmartpriority", [n_blocks])

    def rpc_get_tx_out(self, tx_hash: str, index: int, include_mempool: bool = True) -> Dict[str, Union[str, dict]]:
        """Get the outpoint of a transaction."""
        return self._rpc_post("gettxout", [tx_hash, index, include_mempool])

    def rpc_get_tx_out_set_info(self) -> Dict[str, Union[str, dict]]:
        """Get information about UTXOs from the chain."""
        return self._rpc_post("gettxoutsetinfo")

    def rpc_get_raw_transaction(self, tx_hash: str, verbose: bool = False) -> Dict[str, Union[str, dict]]:
        """Get a raw transaction."""
        return self._rpc_post("getrawtransaction", [tx_hash, verbose])

    def rpc_decode_raw_transaction(self, raw_tx: str) -> Dict[str, Union[str, dict]]:
        """Decode a raw transaction and provide chain info."""
        return self._rpc_post("decoderawtransaction", [raw_tx])

    def rpc_decode_script(self, script: str) -> Dict[str, Union[str, dict]]:
        """Decode a script."""
        return self._rpc_post("decodescript", [script])

    def rpc_send_raw_transaction(self, raw_tx: str) -> Dict[str, Union[str, dict]]:
        """Send a raw transaction without verification."""
        return self._rpc_post("sendrawtransaction", [raw_tx])

    def rpc_create_raw_transaction(self, tx_hash: str, tx_index: int, address: str, amount: float, data: str) -> Dict[str, Union[str, dict]]:
        """Create a raw, unsigned transaction."""
        inputs = [{"txid": tx_hash, "vout": tx_index}]
        outputs = {address: amount, "data": data}
        return self._rpc_post("createrawtransaction", [inputs, outputs])

    def rpc_sign_raw_transaction(self, raw_tx: str, tx_hash: str, tx_index: int, address: str, amount: float, private_key: str) -> Dict[str, Union[str, dict]]:
        """Sign a raw transaction."""
        prevtxs = [{"txid": tx_hash, "vout": tx_index, "address": address, "amount": amount}]
        return self._rpc_post("signrawtransaction", [raw_tx, prevtxs, [private_key]])

    def rpc_get_tx_out_proof(self, tx_id_list: List[str]) -> Dict[str, Union[str, dict]]:
        """Get proof of transaction inclusion (raw MerkleBlock)."""
        return self._rpc_post("gettxoutproof", [tx_id_list])

    def rpc_verify_tx_out_proof(self, proof: str) -> Dict[str, Union[str, dict]]:
        """Verify proof of transaction inclusion."""
        return self._rpc_post("verifytxoutproof", [proof])

    def rpc_get_network_hash_per_sec(self, blocks: int = 120, height: int = -1) -> Dict[str, Union[str, dict]]:
        """Get estimated network hashes per second."""
        return self._rpc_post("getnetworkhashps", [blocks, height])

    def rpc_get_mining_info(self) -> Dict[str, Union[str, dict]]:
        """Get mining information."""
        return self._rpc_post("getmininginfo")

    def rpc_get_work(self, data: Optional[str] = None) -> Dict[str, Union[str, dict]]:
        """Get or submit hashing work for mining."""
        params = [data] if data else []
        return self._rpc_post("getwork", params)

    def rpc_get_work_lp(self) -> Dict[str, Union[str, dict]]:
        """Long polling for new mining work."""
        return self._rpc_post("getworklp")

    def rpc_get_block_template(self) -> Dict[str, Union[str, dict]]:
        """Get a block template or proposal for mining."""
        return self._rpc_post("getblocktemplate")

    def rpc_submit_block(self, block_data: str) -> Dict[str, Union[str, dict]]:
        """Add a block to the chain."""
        return self._rpc_post("submitblock", [block_data])

    def rpc_verify_block(self, block_data: str) -> Dict[str, Union[str, dict]]:
        """Verify block data."""
        return self._rpc_post("verifyblock", [block_data])

    def rpc_set_generate(self, mining: bool = False, proc_limit: int = 0) -> Dict[str, Union[str, dict]]:
        """Start or stop CPU mining."""
        return self._rpc_post("setgenerate", [mining, proc_limit])

    def rpc_get_generate(self) -> Dict[str, Union[str, dict]]:
        """Get the status of mining on the node."""
        return self._rpc_post("getgenerate")

    def rpc_generate(self, num_blocks: int = 1) -> Dict[str, Union[str, dict]]:
        """Mine a specified number of blocks."""
        return self._rpc_post("generate", [num_blocks])

    def rpc_generate_to_address(self, address: str, num_blocks: int = 1) -> Dict[str, Union[str, dict]]:
        """Mine blocks with a specified coinbase address."""
        return self._rpc_post("generatetoaddress", [num_blocks, address])

    def rpc_get_connection_count(self) -> Dict[str, Union[str, dict]]:
        """Get the number of peer connections."""
        return self._rpc_post("getconnectioncount")

    def rpc_ping(self) -> Dict[str, Union[str, dict]]:
        """Send a ping request to all connected peers."""
        return self._rpc_post("ping")

    def rpc_get_peer_info(self) -> Dict[str, Union[str, dict]]:
        """Get information about all connected peers."""
        return self._rpc_post("getpeerinfo")

    def rpc_add_node(self, node_address: str, cmd: str) -> Dict[str, Union[str, dict]]:
        """Add, remove, or try connecting to a node."""
        return self._rpc_post("addnode", [node_address, cmd])

    def rpc_disconnect_node(self, node_address: str) -> Dict[str, Union[str, dict]]:
        """Disconnect a node."""
        return self._rpc_post("disconnectnode", [node_address])

    def rpc_get_added_node_info(self, node_address: str) -> Dict[str, Union[str, dict]]:
        """Get information about a node from the host list."""
        return self._rpc_post("getaddednodeinfo", [node_address])

    def rpc_get_net_totals(self) -> Dict[str, Union[str, dict]]:
        """Get information about used network resources."""
        return self._rpc_post("getnettotals")

    def rpc_get_network_info(self) -> Dict[str, Union[str, dict]]:
        """Get local node's network information."""
        return self._rpc_post("getnetworkinfo")

    def rpc_set_ban(self, node_address: str, cmd: str) -> Dict[str, Union[str, dict]]:
        """Add or remove nodes from the ban list."""
        return self._rpc_post("setban", [node_address, cmd])

    def rpc_list_ban(self) -> Dict[str, Union[str, dict]]:
        """List all banned peers."""
        return self._rpc_post("listbanned")

    def rpc_clear_banned(self) -> Dict[str, Union[str, dict]]:
        """Remove all banned peers."""
        return self._rpc_post("clearbanned")

    def rpc_get_name_info(self, name: str = '') -> Dict[str, Union[str, dict]]:
        """Get information on a given name."""
        return self._rpc_post("getnameinfo", [name])

    def rpc_get_name_by_hash(self, name_hash: str = '') -> Dict[str, Union[str, dict]]:
        """Get the name from a given name hash."""
        return self._rpc_post("getnamebyhash", [name_hash])

    def rpc_get_name_resource(self, name: str = '') -> Dict[str, Union[str, dict]]:
        """Get resource records for a given name."""
        return self._rpc_post("getnameresource", [name])

    def rpc_get_name_proof(self, name: str = '') -> Dict[str, Union[str, dict]]:
        """Get the merkle tree proof for a given name."""
        return self._rpc_post("getnameproof", [name])

    def rpc_send_raw_claim(self, base64_string: str) -> Dict[str, Union[str, dict]]:
        """Send a raw serialized claim (base64-encoded)."""
        return self._rpc_post("sendrawclaim", [base64_string])

    def rpc_get_dnssec_proof(self, name: str = '', estimate: bool = False, verbose: bool = True) -> Dict[str, Union[str, dict]]:
        """Get DNSSEC proof for a domain name."""
        return self._rpc_post("getdnssecproof", [name, estimate, verbose])

    def rpc_send_raw_airdrop(self, base64_string: str = '') -> Dict[str, Union[str, dict]]:
        """Send a raw serialized airdrop (base64-encoded)."""
        return self._rpc_post("sendrawairdrop", [base64_string])

    def rpc_grind_name(self, length: int = 10) -> Dict[str, Union[str, dict]]:
        """Grind a rolled-out available name."""
        return self._rpc_post("grindname", [length])


if __name__ == "__main__":
    try:
        hsd = HSD()
        info = hsd.get_info()
        logger.info(f"Server info: {info}")
        blockchain_info = hsd.rpc_get_blockchain_info()
        logger.info(f"Blockchain info: {blockchain_info}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")