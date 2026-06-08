import json
from datetime import datetime, timedelta

from tests.test_support import ModuleTestCase


class WalletOK:
    def __init__(self, names_response=None, renew_response=None):
        self.names_response = names_response or []
        self.renew_response = renew_response or {"success": True}
        self.renew_calls = []

    def get_wallet_info(self, wallet_id):
        return {"id": wallet_id}

    def get_wallet_names_own(self, wallet_id):
        return self.names_response

    def get_pending_transactions(self, id):
        return []

    def zap_transactions(self, account, id, age):
        return {"zapped": 0}

    def send_renew(self, **kwargs):
        self.renew_calls.append(kwargs["name"])
        return self.renew_response.get(kwargs["name"], {"success": True})

    def get_balance(self, id):
        return {"unconfirmed": 0, "lockedUnconfirmed": 0}

    def get_account_info(self, id):
        return {"receiveAddress": "hs1qmockaddress123456789"}


class WalletMissing:
    def get_wallet_info(self, wallet_id):
        return {"error": "missing"}


class WalletErrors:
    def get_wallet_info(self, wallet_id):
        return {"id": wallet_id}

    def get_wallet_names_own(self, wallet_id):
        return {"error": "boom"}

    def get_pending_transactions(self, id):
        raise RuntimeError("pending failed")

    def zap_transactions(self, account, id, age):
        raise RuntimeError("zap failed")

    def get_balance(self, id):
        raise RuntimeError("balance failed")

    def get_account_info(self, id):
        raise RuntimeError("account failed")


class HSDOK:
    def get_info(self):
        return {"chain": {"height": 123}}


class HSDRaises:
    def get_info(self):
        raise RuntimeError("node down")


class WalletBadType(WalletMissing):
    def get_wallet_info(self, wallet_id):
        return {"id": wallet_id}

    def get_wallet_names_own(self, wallet_id):
        return "bad-response"


class NameManagerTests(ModuleTestCase):
    def _make_manager(self, name_manager, wallet, hsd=None, config_path="config.json"):
        return name_manager.HandshakeNameManager(
            config_path=config_path,
            wallet=wallet,
            hsd=hsd or HSDOK(),
        )

    def test_init_success(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletOK(), HSDOK())

        self.assertEqual(manager.wallet_id, "primary")
        self.assertEqual(manager.threshold_days, 2)
        self.assertEqual(manager.names_file, "wallet_names.json")

    def test_init_raises_when_wallet_missing(self):
        _, name_manager = self.load_modules()

        with self.assertRaisesRegex(RuntimeError, "does NOT exist"):
            self._make_manager(name_manager, WalletMissing(), HSDOK())

    def test_fetch_and_save_names_skips_bad_entries_and_writes_json(self):
        _, name_manager = self.load_modules()
        wallet = WalletOK(
            names_response=[
                {"name": "soon.hns", "renewal": 10, "stats": {"daysUntilExpire": 1}},
                {"name": "missing-stats.hns", "renewal": 11},
                {"name": "bad-days.hns", "renewal": 12, "stats": {"daysUntilExpire": "bad"}},
                {"stats": {"daysUntilExpire": 4}},
                "nope",
            ]
        )
        manager = self._make_manager(name_manager, wallet, HSDOK())
        manager.fetch_and_save_names()

        data = json.loads((self.temp_path / "wallet_names.json").read_text())
        self.assertEqual(set(data), {"soon.hns", "missing-stats.hns", "bad-days.hns"})
        self.assertEqual(data["soon.hns"]["days_until_expire"], 1)
        self.assertIsNone(data["missing-stats.hns"]["days_until_expire"])
        self.assertEqual(data["bad-days.hns"]["days_until_expire"], "bad")

    def test_fetch_and_save_names_raises_on_api_error(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletErrors(), HSDOK())

        with self.assertRaisesRegex(RuntimeError, "Failed to fetch names"):
            manager.fetch_and_save_names()

    def test_fetch_and_save_names_raises_on_unexpected_response_type(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletBadType(), HSDOK())

        with self.assertRaisesRegex(RuntimeError, "unexpected response type"):
            manager.fetch_and_save_names()

    def test_renew_expiring_names_only_renews_due_names_and_skips_bad_records(self):
        _, name_manager = self.load_modules()
        wallet = WalletOK(renew_response={"soon.hns": {"success": True}, "today.hns": {"error": "denied"}})
        manager = self._make_manager(name_manager, wallet, HSDOK())

        names_data = {
            "soon.hns": {
                "expiration_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "renewal_height": 1,
                "days_until_expire": 1,
            },
            "today.hns": {
                "expiration_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "renewal_height": 2,
                "days_until_expire": 2,
            },
            "far.hns": {
                "expiration_date": (datetime.now() + timedelta(days=10)).isoformat(),
                "renewal_height": 3,
                "days_until_expire": 10,
            },
            "bad-date.hns": {
                "expiration_date": "not-an-iso-date",
                "renewal_height": 4,
                "days_until_expire": 4,
            },
            "bad-record.hns": "oops",
        }
        (self.temp_path / "wallet_names.json").write_text(json.dumps(names_data))

        renewed = manager.renew_expiring_names()

        self.assertEqual(wallet.renew_calls, ["soon.hns", "today.hns"])
        self.assertEqual(renewed, ["soon.hns"])

    def test_renew_expiring_names_missing_file_returns_empty(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletOK(), HSDOK())

        self.assertEqual(manager.renew_expiring_names(), [])

    def test_renew_expiring_names_bad_json_returns_empty(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletOK(), HSDOK())
        (self.temp_path / "wallet_names.json").write_text("{")

        self.assertEqual(manager.renew_expiring_names(), [])

    def test_get_status_info_returns_safe_values_on_api_errors(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletErrors(), HSDRaises())
        (self.temp_path / "wallet_names.json").write_text(
            json.dumps({"name.hns": {"expiration_date": datetime.now().isoformat()}})
        )

        status = manager.get_status_info()

        self.assertEqual(status["account"], "primary")
        self.assertEqual(status["block_height"], "Error")
        self.assertEqual(status["balance"], "Error")
        self.assertEqual(status["receiving_address"], "Error")
        self.assertEqual(status["full_receiving_address"], "Error")
        self.assertEqual(status["names_in_wallet"], 1)

    def test_get_soonest_expiring_name_handles_missing_empty_and_valid(self):
        _, name_manager = self.load_modules()
        manager = self._make_manager(name_manager, WalletOK(), HSDOK())

        self.assertEqual(
            manager.get_soonest_expiring_name(),
            {"name": None, "expiration_date": None, "days_until_expire": None},
        )

        (self.temp_path / "wallet_names.json").write_text(json.dumps({}))
        self.assertEqual(
            manager.get_soonest_expiring_name(),
            {"name": None, "expiration_date": None, "days_until_expire": None},
        )

        (self.temp_path / "wallet_names.json").write_text(
            json.dumps(
                {
                    "later.hns": {"expiration_date": (datetime.now() + timedelta(days=5)).isoformat()},
                    "soon.hns": {"expiration_date": (datetime.now() + timedelta(days=1)).isoformat()},
                }
            )
        )
        soonest = manager.get_soonest_expiring_name()
        self.assertEqual(soonest["name"], "soon.hns")
        self.assertIsNotNone(soonest["expiration_date"])
