# tests/unit_mock_tests/test_channel_zap.py
import pytest
import numpy as np
from analysis.av_quality import AVQualityChecker
from analysis.timing import TimingEngine


class TestChannelZapUnit:
    """
    Unit tests — no hardware needed.
    Uses mock_backend from tests/unit_mock_tests/conftest.py
    """
    @pytest.mark.unit_mock
    def test_send_key_ch_up_recorded(self, mock_backend):
        mock_backend.send_key("CH_UP")
        assert "CH_UP" in mock_backend.keys_pressed()

    @pytest.mark.unit_mock
    def test_key_sequence_order(self, mock_backend):
        keys = ["CH_UP", "CH_UP", "VOL_UP", "OK"]
        for k in keys:
            mock_backend.send_key(k)
        assert mock_backend.keys_pressed() == keys

    @pytest.mark.unit_mock
    def test_live_frame_not_black(self, mock_backend, av):
        mock_backend.set_live_screen()
        frame         = mock_backend.grab_frame()
        is_black, pct = av.is_black_screen(frame)
        assert not is_black, f"Live frame should not be black ({pct*100:.1f}%)"

    @pytest.mark.unit_mock
    def test_black_screen_detected(self, mock_backend_black, av):
        frame         = mock_backend_black.grab_frame()
        is_black, pct = av.is_black_screen(frame)
        assert is_black, "Black frame should be detected"

    @pytest.mark.unit_mock
    def test_frame_changes_after_channel_switch(self, mock_backend, timer):
        mock_backend.set_black_screen()
        baseline = mock_backend.grab_frame()

        mock_backend.set_live_screen()

        changed, elapsed_ms, new_frame = timer.wait_for_frame_change(
            grab_frame_fn  = mock_backend.grab_frame,
            baseline_frame = baseline,
            threshold      = 0.05,
            timeout        = 5,
            poll_interval  = 0
        )
        assert changed,          "Frame should change after channel loads"
        assert new_frame is not None

    @pytest.mark.unit_mock
    def test_zap_time_measured(self, mock_backend, av, timer):
        call_count = [0]

        def grab():
            call_count[0] += 1
            if call_count[0] >= 3:
                mock_backend.set_live_screen()
            return mock_backend.grab_frame()

        success, zap_ms = timer.measure_zap_time(
            grab_frame_fn = grab,
            send_key_fn   = mock_backend.send_key,
            key           = "CH_UP",
            detect_fn     = lambda f: not av.is_black_screen(f)[0],
            timeout       = 5
        )
        assert success,   "Zap should succeed when channel loads"
        assert zap_ms > 0

    @pytest.mark.unit_mock
    def test_video_not_frozen(self, mock_backend, av):
        mock_backend.set_live_screen()
        frame1 = mock_backend.grab_frame()

        # Create a clearly different deterministic frame
        frame2 = 255 - frame1

        mock_backend.set_custom_frame(frame2)
        frame2           = mock_backend.grab_frame()
        is_frozen, score = av.is_frozen(frame1, frame2)
        assert not is_frozen, f"Different frames should not be frozen (score={score:.4f})"

    @pytest.mark.unit_mock
    def test_frozen_detected_on_identical_frames(self, mock_backend, av):
        mock_backend.set_live_screen()
        frame1           = mock_backend.grab_frame()
        frame2           = mock_backend.grab_frame()
        is_frozen, score = av.is_frozen(frame1, frame2)
        assert is_frozen, f"Identical frames should be frozen (score={score:.4f})"

    @pytest.mark.unit_mock
    def test_device_info_mock(self, mock_backend):
        info = mock_backend.get_device_info()
        assert info.is_connected is True
        assert info.backend      == "mock"

    @pytest.mark.unit_mock
    def test_clear_history(self, mock_backend):
        mock_backend.send_key("CH_UP")
        mock_backend.send_key("CH_DOWN")
        mock_backend.clear_history()
        assert mock_backend.keys_pressed() == []