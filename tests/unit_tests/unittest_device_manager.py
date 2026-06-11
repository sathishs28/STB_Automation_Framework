import unittest
from unittest.mock import patch, MagicMock, mock_open
import io
from core.redrat.exceptions import ConnectionError


class Test_Device_Manager(unittest.TestCase):

    # Fake devices.yaml content
    fake_yaml = """
    active_device: ovt_stb
    devices:
    ovt_stb:
    backend: ir
    key_map: key_map_ovt_comon_remote
"""

    # Test 1 — startup loads config correctly
    @patch("builtins.open", new_callable=mock_open, read_data="""active_device: ovt_stb
devices:
  ovt_stb:
    backend: ir
    key_map: key_map_ovt_comon_remote
""")
    @patch("backends.ir_backend.IR_Backend")
    def test_startup_loads_correct_device(self, mock_backend, mock_file):
        from core.device_manager import Device_Manager

        mock_backend.return_value.get_device_info.return_value = MagicMock(
            is_connected=True,
            device_id="RedRat-X%2024103",
            dataset="OVT_NXT_Digital_Remote",
            backend="ir"
        )

        dm = Device_Manager()
        dm._load_config()
        self.assertEqual(dm.device_name, "ovt_stb")

    # Test 2 — health check fails when hub is down
    @patch("builtins.open", new_callable=mock_open, read_data="""active_device: ovt_stb
devices:
  ovt_stb:
    backend: ir
    key_map: key_map_ovt_comon_remote
""")
    def test_health_check_fails_when_disconnected(self, mock_file):
        from core.device_manager import Device_Manager

        dm = Device_Manager()
        dm._load_config()

        mock_backend = MagicMock()
        mock_backend.get_device_info.return_value = MagicMock(is_connected=False)
        dm.backend = mock_backend

        with self.assertRaises(ConnectionError):
            dm._health_check(retries=2, delay_seconds=0)  # Reduced for testing


if __name__ == "__main__":
    unittest.main(verbosity=2)