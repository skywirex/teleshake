import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from api.hsd import HSD
from api.wallet import WALLET


class HandshakeNameManager:
    """
    A class to manage Handshake (HNS) domain names:
    - Fetch owned names
    - Track expiration dates
    - Auto-renew names nearing expiration
    - Provide status info
    """

    DEFAULT_CONFIG = {
        "RENEWAL_THRESHOLD_DAYS": 30,
        "WALLET_ID": "primary",
        "WALLET_PASSPHRASE": "",
        "NAMES_JSON_FILE": "wallet_names.json"
    }

    def __init__(
        self,
        config_path: str = "config.json",
        wallet: Optional[WALLET] = None,
        hsd: Optional[HSD] = None
    ):
        # Initialize API clients
        self.wallet = wallet or WALLET()
        self.hsd = hsd or HSD()

        # Load Config
        try:
            self.config = self._load_config(config_path)
        except FileNotFoundError:
            print(f"Config file '{config_path}' not found. Using defaults.")
            self.config = {}

        # Set Configurable values (Merge loaded config with defaults)
        self.threshold_days = self.config.get("RENEWAL_THRESHOLD_DAYS", self.DEFAULT_CONFIG["RENEWAL_THRESHOLD_DAYS"])
        self.wallet_id = self.config.get("WALLET_ID", self.DEFAULT_CONFIG["WALLET_ID"])
        self.passphrase = self.config.get("WALLET_PASSPHRASE", self.DEFAULT_CONFIG["WALLET_PASSPHRASE"])
        self.names_file = self.config.get("NAMES_JSON_FILE", self.DEFAULT_CONFIG["NAMES_JSON_FILE"])

        # Validate wallet immediately
        self.check_wallet_exists()

    @staticmethod
    def _load_config(config_path: str) -> Dict[str, Any]:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file {config_path} not found")
        with open(config_path, 'r') as f:
            return json.load(f)

    def check_wallet_exists(self) -> None:
        """Raise error if wallet doesn't exist (no auto-creation)."""
        response = self.wallet.get_wallet_info(self.wallet_id)
        # Guard for non-dict responses from the wallet API
        if not isinstance(response, dict) or "error" in response:
            error_text = response.get('error') if isinstance(response, dict) else str(response)
            error_msg = (
                f"Wallet '{self.wallet_id}' does NOT exist.\n"
                f"Import the Wallet first manually first using `curl` command provided in the README file. Error: {error_text}"
            )
            # Log error but don't crash init if strictly just checking
            print(error_msg)
            raise RuntimeError(error_msg)
        print(f"Wallet '{self.wallet_id}' is ready.")

    def _get_expiration_date(self, name_info: Dict[str, Any]) -> datetime:
        # Ensure name_info is a dict before using .get()
        if not isinstance(name_info, dict):
            print("Warning: name_info is not a dict; assuming far future")
            return datetime.now() + timedelta(days=730)

        stats = name_info.get("stats", {})
        if not isinstance(stats, dict):
            stats = {}

        days_until_expire = stats.get("daysUntilExpire")
        if days_until_expire is None:
            name_display = name_info.get("name", "<unknown>")
            print(f"Warning: No expiration data for '{name_display}', assuming far future")
            return datetime.now() + timedelta(days=730)

        return datetime.now() + timedelta(days=days_until_expire)

    def fetch_and_save_names(self) -> None:
        """Fetch all owned names from wallet and save to JSON with expiration info."""
        response = self.wallet.get_wallet_names_own(self.wallet_id)
        if "error" in response:
            raise RuntimeError(f"Failed to fetch names: {response['error']}")

        names_data = {}
        for name_info in response:
            if not isinstance(name_info, dict):
                print("Warning: Skipping non-dict entry in names response")
                continue

            name = name_info.get("name")
            if not name:
                print("Warning: Skipping entry with missing 'name' key")
                continue
            try:
                expiration_date = self._get_expiration_date(name_info)
                names_data[name] = {
                    "expiration_date": expiration_date.isoformat(),
                    "renewal_height": name_info.get("renewal", 0),
                    "days_until_expire": (name_info.get("stats") or {}).get("daysUntilExpire"),
                }
            except Exception as e:
                print(f"Error processing '{name}': {e}")

        with open(self.names_file, 'w') as f:
            json.dump(names_data, f, indent=4)
        print(f"Saved {len(names_data)} names to {self.names_file}")

    def load_names(self) -> Dict[str, Any]:
        """Load names from JSON file."""
        if not os.path.exists(self.names_file):
            raise FileNotFoundError(f"{self.names_file} not found. Run fetch_and_save_names() first.")
        with open(self.names_file, 'r') as f:
            return json.load(f)

    def renew_expiring_names(self) -> List[str]:
        """Renew all names expiring within RENEWAL_THRESHOLD_DAYS. Returns renewed names."""
        try:
            names_data = self.load_names()
        except FileNotFoundError:
            print("No names file found. Please fetch names first.")
            return []

        threshold_date = datetime.now() + timedelta(days=self.threshold_days)
        renewed = []

        for name, data in names_data.items():
            exp_date = datetime.fromisoformat(data["expiration_date"])
            if exp_date <= threshold_date:
                print(f"Renewing '{name}' — expires {exp_date.date()}")
                result = self.wallet.send_renew(
                    id=self.wallet_id,
                    passphrase=self.passphrase,
                    name=name,
                    sign=True,
                    broadcast=True
                )
                if "error" in result:
                    print(f"Failed to renew '{name}': {result['error']}")
                else:
                    renewed.append(name)
                    print(f"Successfully renewed '{name}'")

        return renewed

    def get_status_info(self) -> Dict[str, Any]:
        """Get node, wallet balance, and receive address."""
        info = {"account": self.wallet_id}

        # Node info
        node_info = self.hsd.get_info()
        if not isinstance(node_info, dict) or "error" in node_info:
            info["block_height"] = "Error"
        else:
            info["block_height"] = node_info.get("chain", {}).get("height", "Unknown")

        # Balance
        balance_info = self.wallet.get_balance(id=self.wallet_id)
        if not isinstance(balance_info, dict) or "error" in balance_info:
            info["balance"] = "Error"
        else:
            spendable = (balance_info.get("unconfirmed", 0) - balance_info.get("lockedUnconfirmed", 0)) / 1_000_000
            info["balance"] = round(spendable, 6)

        # Receive address
        acct_info = self.wallet.get_account_info(id=self.wallet_id)
        if not isinstance(acct_info, dict) or "error" in acct_info:
            full_addr = "Error"
        else:
            full_addr = acct_info.get("receiveAddress", "Error")

        info["receiving_address"] = f"{full_addr[:8]}...{full_addr[-6:]}" if full_addr != "Error" else "Error"
        info["full_receiving_address"] = full_addr

        return info

    def get_soonest_expiring_name(self) -> Dict[str, Optional[Any]]:
        """Return the name that will expire soonest."""
        if not os.path.exists(self.names_file):
            return {"name": None, "expiration_date": None, "days_until_expire": None}

        try:
            names_data = self.load_names()
        except FileNotFoundError:
            return {"name": None, "expiration_date": None, "days_until_expire": None}

        if not names_data:
            return {"name": None, "expiration_date": None, "days_until_expire": None}

        soonest_name = None
        soonest_date = None

        for name, data in names_data.items():
            exp_date = datetime.fromisoformat(data["expiration_date"])
            if soonest_date is None or exp_date < soonest_date:
                soonest_date = exp_date
                soonest_name = name

        days_left = (soonest_date - datetime.now()).days if soonest_date else None

        return {
            "name": soonest_name,
            "expiration_date": soonest_date.strftime("%Y-%m-%d %H:%M") if soonest_date else None,
            "days_until_expire": days_left
        }


# ==========================================
# TEST BLOCK (Mocks included for verification)
# ==========================================
if __name__ == "__main__":
    # 1. Setup Dummy Config
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as f:
            json.dump({
                "RENEWAL_THRESHOLD_DAYS": 30,
                "WALLET_ID": "primary",
                "WALLET_PASSPHRASE": "test"
            }, f)

    # 2. Define Mock Classes for testing without live API
    class MockWallet:
        def get_wallet_info(self, wallet_id):
            return {"id": wallet_id}
        def get_wallet_names_own(self, wallet_id):
            return [{"name": "test.hns", "renewal": 123, "stats": {"daysUntilExpire": 10}}]
        def send_renew(self, id, passphrase, name, sign, broadcast):
            return {"success": True}
        def get_balance(self, id):
            return {"unconfirmed": 123500000, "lockedUnconfirmed": 0}
        def get_account_info(self, id):
            return {"receiveAddress": "hs1qmockaddress123456789"}

    class MockHSD:
        def get_info(self):
            return {"chain": {"height": 268271}}

    # 3. Initialize Manager with Mocks
    print(">>> Initializing HandshakeNameManager with Mock APIs...")
    # Passing mocks directly to bypass actual API calls
    manager = HandshakeNameManager(wallet=MockWallet(), hsd=MockHSD())

    # 4. Run through functionality
    print("\n--- Fetching names ---")
    manager.fetch_and_save_names()

    print("\n--- Current Status ---")
    print(json.dumps(manager.get_status_info(), indent=2))

    print("\n--- Soonest Expiring Name ---")
    print(manager.get_soonest_expiring_name())

    # Inject expiring data to test renewal
    print("\n--- Simulating Expiring Name ---")
    mock_names_data = {
        "urgent.hns": {
            "expiration_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "renewal_height": 999,
            "days_until_expire": 5
        }
    }
    with open('wallet_names.json', 'w') as f:
        json.dump(mock_names_data, f)

    print("\n--- Renewing names nearing expiration ---")
    renewed = manager.renew_expiring_names()
    print(f"Renewed names: {renewed}")

    # Cleanup
    if os.path.exists('config.json'):
        os.remove('config.json')