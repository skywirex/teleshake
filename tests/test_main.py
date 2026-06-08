from tests.test_support import ModuleTestCase


class DummyWalletBase:
    def list_wallets(self):
        return ["primary", "secondary"]


class DummyWalletSuccess(DummyWalletBase):
    def unlock_wallet(self, passphrase, id, timeout=0):
        return {"success": True}


class DummyWalletFail(DummyWalletBase):
    def unlock_wallet(self, passphrase, id, timeout=0):
        return {"success": False}


class DummyWalletError(DummyWalletBase):
    def unlock_wallet(self, passphrase, id, timeout=0):
        raise RuntimeError("wallet down")


class DummyHSD:
    pass


class FakeManager:
    def __init__(self, config_path, wallet, hsd):
        self.config_path = config_path
        self.wallet = wallet
        self.hsd = hsd
        self.threshold_days = 2

    def fetch_and_save_names(self):
        return None

    def renew_expiring_names(self):
        return ["soon.hns"]

    def get_status_info(self):
        return {
            "account": "primary",
            "block_height": 123,
            "balance": 1.23,
            "names_in_wallet": 2,
            "full_receiving_address": "hs1qmockaddress123456789",
        }

    def get_soonest_expiring_name(self):
        return {
            "name": "soon.hns",
            "expiration_date": "2026-01-01 00:00",
            "days_until_expire": 1,
        }


class BrokenManager:
    def __init__(self, config_path, wallet, hsd):
        raise RuntimeError("manager init failed")


class MainTests(ModuleTestCase):
    def test_main_triggers_setup_flow_and_reloads_config(self):
        main, _ = self.load_modules()
        sent_messages = []
        setup_calls = []
        load_configs = [
            {"WALLET_ID": "primary", "WALLET_PASSPHRASE": "old"},
            {"WALLET_ID": "active", "WALLET_PASSPHRASE": "new"},
        ]

        def fake_load_config():
            return load_configs.pop(0)

        self.patch_attr(main, "load_config", fake_load_config)
        self.patch_attr(main, "send_telegram_message", lambda message, parse_mode=None: sent_messages.append((message, parse_mode)))
        self.patch_attr(main, "interactive_wallet_setup", lambda wallet, wallets: setup_calls.append((wallet, wallets)) or True)
        self.patch_attr(main, "WALLET", DummyWalletSuccess)
        self.patch_attr(main, "HSD", DummyHSD)
        self.patch_attr(main, "HandshakeNameManager", FakeManager)

        main.main()

        self.assertEqual(len(setup_calls), 1)
        self.assertIsInstance(setup_calls[0][0], DummyWalletSuccess)
        self.assertTrue(any("TeleShake Update" in message for message, _ in sent_messages))

    def test_main_handles_config_load_failure(self):
        main, _ = self.load_modules()
        sent_messages = []
        setup_calls = []

        def fake_load_config():
            raise RuntimeError("config missing")

        self.patch_attr(main, "load_config", fake_load_config)
        self.patch_attr(main, "send_telegram_message", lambda message, parse_mode=None: sent_messages.append((message, parse_mode)))
        self.patch_attr(main, "interactive_wallet_setup", lambda wallet, wallets: setup_calls.append((wallet, wallets)) or False)
        self.patch_attr(main, "WALLET", DummyWalletSuccess)
        self.patch_attr(main, "HSD", DummyHSD)

        main.main()

        self.assertEqual(len(setup_calls), 1)
        self.assertTrue(any("Config load FAILED" in message for message, _ in sent_messages))

    def test_main_reports_wallet_verification_failure(self):
        main, _ = self.load_modules({"WALLET_ID": "active", "WALLET_PASSPHRASE": "wrong"})
        sent_messages = []
        setup_calls = []

        self.patch_attr(main, "load_config", lambda: {"WALLET_ID": "active", "WALLET_PASSPHRASE": "wrong"})
        self.patch_attr(main, "send_telegram_message", lambda message, parse_mode=None: sent_messages.append((message, parse_mode)))
        self.patch_attr(main, "interactive_wallet_setup", lambda wallet, wallets: setup_calls.append((wallet, wallets)) or False)
        self.patch_attr(main, "WALLET", DummyWalletFail)
        self.patch_attr(main, "HSD", DummyHSD)

        main.main()

        self.assertEqual(len(setup_calls), 1)
        self.assertTrue(any("Wallet verification FAILED" in message for message, _ in sent_messages))

    def test_main_reports_wallet_verification_exception(self):
        main, _ = self.load_modules({"WALLET_ID": "active", "WALLET_PASSPHRASE": "wrong"})
        sent_messages = []
        setup_calls = []

        self.patch_attr(main, "load_config", lambda: {"WALLET_ID": "active", "WALLET_PASSPHRASE": "wrong"})
        self.patch_attr(main, "send_telegram_message", lambda message, parse_mode=None: sent_messages.append((message, parse_mode)))
        self.patch_attr(main, "interactive_wallet_setup", lambda wallet, wallets: setup_calls.append((wallet, wallets)) or False)
        self.patch_attr(main, "WALLET", DummyWalletError)
        self.patch_attr(main, "HSD", DummyHSD)

        main.main()

        self.assertEqual(len(setup_calls), 1)
        self.assertTrue(any("Node Connection/Verification ERROR" in message for message, _ in sent_messages))

    def test_main_reports_manager_init_failure(self):
        main, _ = self.load_modules({"WALLET_ID": "active", "WALLET_PASSPHRASE": "correct"})
        sent_messages = []

        self.patch_attr(main, "load_config", lambda: {"WALLET_ID": "active", "WALLET_PASSPHRASE": "correct"})
        self.patch_attr(main, "send_telegram_message", lambda message, parse_mode=None: sent_messages.append((message, parse_mode)))
        self.patch_attr(main, "WALLET", DummyWalletSuccess)
        self.patch_attr(main, "HSD", DummyHSD)
        self.patch_attr(main, "HandshakeNameManager", BrokenManager)

        main.main()

        self.assertTrue(any("Wallet Manager Initialization FAILED" in message for message, _ in sent_messages))
