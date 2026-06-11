import unittest
import requests
from unittest.mock import patch, MagicMock
from core.redrat.exceptions import ConnectionError, IRTransmitError
from core.redrat.redrat_client import RedRat_Client

class Test_RedRat_Client_Config(unittest.TestCase):

    # Test 1 — all .env values load correctly
    @patch.dict("os.environ", {
        "REDRAT_HUB_URL"     : "http://127.0.0.1:8080",
        "REDRAT_DEVICE_ID"   : "RedRat-X%2024103",
        "REDRAT_OUTPUT_PORT" : "4",
        "REDRAT_DATASET"     : "OVT_NXT_Digital_Remote",
        "REDRAT_TIMEOUT_MS"  : "5000",
        "REDRAT_RETRY_COUNT" : "3",
    })
    def test_config_loads_correctly(self):
        client = RedRat_Client()
        self.assertEqual(client.hub_url,     "http://127.0.0.1:8080")
        self.assertEqual(client.device_id,   "RedRat-X%2024103")
        self.assertEqual(client.output_port, "4")
        self.assertEqual(client.dataset,     "OVT_NXT_Digital_Remote")
        self.assertEqual(client.timeout,     5.0)
        self.assertEqual(client.retry_count, 3)

    # Test 2 — missing .env value raises EnvironmentError
    @patch.dict("os.environ", {
        "REDRAT_HUB_URL"  : "http://127.0.0.1:8080",
        "REDRAT_DEVICE_ID": "RedRat-X%2024103",
        # REDRAT_OUTPUT_PORT intentionally missing
        "REDRAT_DATASET"  : "OVT_NXT_Digital_Remote",
    }, clear=True)
    def test_missing_env_raises_error(self):
        with self.assertRaises(EnvironmentError) as ctx:
            RedRat_Client()
        self.assertIn("REDRAT_OUTPUT_PORT", str(ctx.exception))

class Test_RedRat_Client_GET(unittest.TestCase):

    # ✅ Fixed — all four required values present
    valid_env = {
        "REDRAT_HUB_URL"     : "http://127.0.0.1:8080",
        "REDRAT_DEVICE_ID"   : "RedRat-X%2024103",
        "REDRAT_OUTPUT_PORT" : "4",
        "REDRAT_DATASET"     : "OVT_NXT_Digital_Remote",
    }

    # Test 3 — get_devices() returns device list
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.get")   # ✅ fixed patch path
    def test_get_devices_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"id": "RedRat-X%2024103"}]
        mock_get.return_value.raise_for_status = MagicMock()

        client = RedRat_Client()
        result = client.get_devices()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "RedRat-X%2024103")

    # Test 4 — get_signals() returns signal names
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.get")   # ✅ fixed patch path
    def test_get_signals_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = ["VOL+", "VOL-", "CH_UP", "CH_DOWN", "OK"]
        mock_get.return_value.raise_for_status = MagicMock()

        client = RedRat_Client()
        signals = client.get_signals()
        self.assertIn("CH_UP", signals)
        self.assertIn("OK", signals)

    # Test 5 — health_check() returns False when hub is down
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.get",   # ✅ fixed patch path
           side_effect=requests.exceptions.ConnectionError)
    def test_health_check_fails_when_hub_down(self, mock_get):
        client = RedRat_Client()
        result = client.health_check()
        self.assertFalse(result)


class Test_RedRat_Client_POST(unittest.TestCase):

    valid_env = {
        "REDRAT_HUB_URL"     : "http://127.0.0.1:8080",
        "REDRAT_DEVICE_ID"   : "RedRat-X%2024103",
        "REDRAT_OUTPUT_PORT" : "4",
        "REDRAT_DATASET"     : "OVT_NXT_Digital_Remote",
    }

    # Test 6 — successful signal send
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.post")  # ✅ fixed patch path
    def test_send_signal_success(self, mock_post):
        mock_post.return_value.status_code = 200

        client = RedRat_Client()
        result = client.send_signal("VOL+")
        self.assertTrue(result)

    # Test 7 — bad signal name raises IRTransmitError
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.post")  # ✅ fixed patch path
    def test_send_signal_bad_name(self, mock_post):
        mock_post.return_value.status_code = 404

        client = RedRat_Client()
        with self.assertRaises(IRTransmitError):
            client.send_signal("INVALID_KEY")

    # Test — signal name not found returns IRTransmitError (not ConnectionError)
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.post")
    def test_send_signal_not_in_dataset(self, mock_post):
        mock_post.return_value.status_code = 500

        client = RedRat_Client()
        with self.assertRaises(IRTransmitError):
            client.send_signal("WRONG_SIGNAL_NAME")
    # Test 8 — hub down raises ConnectionError
    @patch.dict("os.environ", valid_env)
    @patch("core.redrat.redrat_client.requests.post",  # ✅ fixed patch path
           side_effect=requests.exceptions.ConnectionError)
    def test_send_signal_hub_down(self, mock_post):
        client = RedRat_Client()
        with self.assertRaises(ConnectionError):
            client.send_signal("VOL+")

if __name__ == "__main__":
    unittest.main(verbosity=2)