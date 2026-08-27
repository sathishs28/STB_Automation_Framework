# tests/unit_tests/unittest_timing.py
import unittest
import time
import numpy as np
import cv2
from analysis.timing import TimingEngine


class Test_TimingEngine(unittest.TestCase):

    def setUp(self):
        self.timer = TimingEngine()

        # Normal frame with content
        self.frame_a = np.ones((720, 1280, 3), dtype=np.uint8) * 100
        cv2.rectangle(self.frame_a, (100, 100), (400, 300), (255, 255, 255), -1)

        # Different frame — simulates channel change
        self.frame_b = np.ones((720, 1280, 3), dtype=np.uint8) * 50
        cv2.rectangle(self.frame_b, (500, 400), (900, 600), (0, 200, 0), -1)

    # Test 1 — timer measures roughly correct duration
    def test_timer_accuracy(self):
        self.timer.start()
        time.sleep(0.2)
        elapsed = self.timer.stop()
        self.assertGreater(elapsed, 180)   # at least 180ms
        self.assertLess(elapsed, 300)      # no more than 300ms

    # Test 2 — stop without start raises error
    def test_stop_without_start_raises_error(self):
        with self.assertRaises(RuntimeError):
            self.timer.stop()

    # Test 3 — frame change detected
    def test_wait_for_frame_change_detected(self):
        frames   = [self.frame_a, self.frame_a, self.frame_b]
        call_idx = [0]

        def grab():
            frame = frames[min(call_idx[0], len(frames)-1)]
            call_idx[0] += 1
            return frame

        changed, elapsed_ms, new_frame = self.timer.wait_for_frame_change(
            grab_frame_fn  = grab,
            baseline_frame = self.frame_a,
            threshold      = 0.01,
            timeout        = 5,
            poll_interval  = 0
        )
        self.assertTrue(changed)
        self.assertIsNotNone(new_frame)

    # Test 4 — no change detected within timeout
    def test_wait_for_frame_change_timeout(self):
        def grab():
            return self.frame_a   # always same frame

        changed, elapsed_ms, new_frame = self.timer.wait_for_frame_change(
            grab_frame_fn  = grab,
            baseline_frame = self.frame_a,
            threshold      = 0.5,  # very high threshold — never met
            timeout        = 0.3,
            poll_interval  = 0.1
        )
        self.assertFalse(changed)
        self.assertIsNone(new_frame)

    # Test 5 — measure_zap_time succeeds immediately
    def test_measure_zap_time_success(self):
        def grab():
            return self.frame_b

        def send_key(key):
            pass   # no-op in test

        success, elapsed = self.timer.measure_zap_time(
            grab_frame_fn = grab,
            send_key_fn   = send_key,
            key           = "CH_UP",
            detect_fn     = lambda f: True,   # always detected
            timeout       = 5
        )
        self.assertTrue(success)
        self.assertGreater(elapsed, 0)

    # Test 6 — measure_zap_time timeout
    def test_measure_zap_time_timeout(self):
        def grab():
            return self.frame_a

        def send_key(key):
            pass

        success, elapsed = self.timer.measure_zap_time(
            grab_frame_fn = grab,
            send_key_fn   = send_key,
            key           = "CH_UP",
            detect_fn     = lambda f: False,  # never detected
            timeout       = 0.3
        )
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main(verbosity=2)