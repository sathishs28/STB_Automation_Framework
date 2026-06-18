# tests/unit_tests/unittest_av_quality.py
import unittest
import numpy as np
import cv2
from analysis.av_quality import AVQualityChecker


class Test_AVQualityChecker(unittest.TestCase):

    def setUp(self):
        self.av = AVQualityChecker()

        # Normal frame — grey with some content
        self.normal_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 128
        cv2.imwrite("temp/unittest_av_quality_normal_frame.png", self.normal_frame)
        cv2.rectangle(self.normal_frame, (100, 100), (400, 300), (255, 255, 255), -1)
        cv2.rectangle(self.normal_frame, (600, 200), (900, 500), (0, 0, 200), -1)
        cv2.imwrite("temp/unittest_av_quality_normal_frame.png", self.normal_frame)
        # Black frame — all zeros
        self.black_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Uniform frame — no signal (flat colour)
        self.uniform_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 30
        cv2.imwrite("temp/unittest_av_quality_uniform_frame.png", self.uniform_frame)

    # Test 1 — black frame detected
    def test_is_black_screen_true(self):
        is_black, pct = self.av.is_black_screen(self.black_frame)
        self.assertTrue(is_black)
        self.assertGreaterEqual(pct, 0.98)

    # Test 2 — normal frame not black
    def test_is_black_screen_false(self):
        is_black, pct = self.av.is_black_screen(self.normal_frame)
        self.assertFalse(is_black)

    # Test 3 — identical frames = frozen
    def test_is_frozen_identical_frames(self):
        is_frozen, score = self.av.is_frozen(self.normal_frame, self.normal_frame)
        self.assertTrue(is_frozen)
        self.assertAlmostEqual(score, 1.0, places=2)

    # Test 4 — different frames = not frozen
    def test_is_frozen_different_frames(self):
        different_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        is_frozen, score = self.av.is_frozen(self.normal_frame, different_frame)
        self.assertFalse(is_frozen)

    # Test 5 — normal frame = signal present
    def test_is_no_signal_false(self):
        no_signal, reason = self.av.is_no_signal(self.normal_frame, self.uniform_frame)
        self.assertFalse(no_signal)

    # Test 6 — health check healthy frame
    def test_check_video_health_healthy(self):
        # Slightly different second frame — simulates moving video
        frame2        = self.normal_frame.copy()
        frame2[50:60] = 200
        result        = self.av.check_video_health(self.normal_frame, frame2)
        self.assertTrue(result["healthy"])
        self.assertFalse(result["black_screen"])
        self.assertFalse(result["frozen"])

    # Test 7 — health check black screen
    def test_check_video_health_black(self):
        result = self.av.check_video_health(self.black_frame, self.black_frame)
        self.assertFalse(result["healthy"])
        self.assertTrue(result["black_screen"])


if __name__ == "__main__":
    unittest.main(verbosity=2)