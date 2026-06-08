import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULES_TO_CLEAR = ["main", "name_manager", "bot_telegram", "api", "api.hsd", "api.wallet"]
BASE_CONFIG = {
    "NODE_API_KEY": "node-api-key",
    "WALLET_API": "wallet-api-key",
    "WALLET_ID": "primary",
    "WALLET_PASSPHRASE": "test-passphrase",
    "RENEWAL_THRESHOLD_DAYS": 2,
    "NAMES_JSON_FILE": "wallet_names.json",
}


def clear_modules() -> None:
    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)


def install_bot_telegram_stub() -> None:
    stub = ModuleType("bot_telegram")

    def send_telegram_message(message, parse_mode=None):
        return None

    def interactive_wallet_setup(wallet_instance, wallets):
        return False

    def load_config():
        return {}

    stub.send_telegram_message = send_telegram_message
    stub.interactive_wallet_setup = interactive_wallet_setup
    stub.load_config = load_config
    sys.modules["bot_telegram"] = stub


class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self._tmpdir.name)
        self._original_cwd = Path.cwd()
        self._original_sys_path = list(sys.path)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        os.chdir(self._original_cwd)
        sys.path[:] = self._original_sys_path
        clear_modules()
        self._tmpdir.cleanup()

    def load_modules(self, extra_config=None):
        config = dict(BASE_CONFIG)
        if extra_config:
            config.update(extra_config)

        (self.temp_path / "config.json").write_text(json.dumps(config))
        os.chdir(self.temp_path)
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        clear_modules()
        install_bot_telegram_stub()

        main = importlib.import_module("main")
        name_manager = importlib.import_module("name_manager")
        return main, name_manager

    def patch_attr(self, obj, attr, value):
        original = getattr(obj, attr)
        setattr(obj, attr, value)
        self.addCleanup(lambda: setattr(obj, attr, original))
