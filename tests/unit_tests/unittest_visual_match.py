# tests/unit_tests/unittest_visual_match.py
import unittest
import numpy as np
import cv2
import os
from analysis.visual_match import VisualMatcher
from core.temp_manager import TempManager
from core.logger import setup_logging

# Setup logging
setup_logging()

class Test_VisualMatcher(unittest.TestCase):

    def setUp(self):
        self.frame = np.ones((720, 1280, 3), dtype=np.uint8) * 200
        cv2.rectangle(
            self.frame,
            (100, 100),
            (200, 150),
            (0, 0, 0),
            -1
        )
        
        cv2.circle(
            self.frame,
            (150, 125),
            15,
            (255, 255, 255),
            -1
        )
        
        # Create a temporary subfolder for unit test templates
        self.temp_dir = TempManager.create_temp_dir(subfolder="unit_tests_visual_match")
        if not os.path.exists(self.temp_dir):
            raise FileNotFoundError(f"Failed to create temp subfolder: {self.temp_dir}")

        self.template_path = os.path.join(self.temp_dir, "unittest_test_template.png")
        template = self.frame[100:150, 100:200]
        cv2.imwrite(self.template_path, template)

        self.matcher = VisualMatcher(threshold=0.85)

    # Test 1 — template found in frame
    def test_match_found(self):
        found, score, location = self.matcher.match(self.frame, self.template_path)
        self.assertTrue(found)
        self.assertGreaterEqual(score, 0.85)
        self.assertIsNotNone(location)

    # Test 2 — template NOT found in genuinely different frame
    def test_match_not_found(self):
        # ✅ Random noise — genuinely different from template
        rng         = np.random.default_rng(42)
        noise_frame = rng.integers(0, 255, (720, 1280, 3), dtype=np.uint8)

        # Save full frame as template — should be rejected
    
        noise_template_path = os.path.join(self.temp_dir, "unittest_noise_full_frame.png")
        cv2.imwrite(noise_template_path, noise_frame)  # Save noise frame as template for debugging
        
        found, score, location = self.matcher.match(noise_frame, self.template_path)
        self.assertFalse(found)
        self.assertIsNone(location)

    # Test 3 — missing template raises FileNotFoundError
    def test_missing_template_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            self.matcher.match(self.frame, os.path.join(self.temp_dir, "unittest_nonexistent.png")) 

    # Test 4 — region match works
    def test_match_region(self):
        region = (50, 50, 300, 200)
        found, score, location = self.matcher.match_region(
            self.frame, self.template_path, region
        )
        self.assertTrue(found)

    # Test 5 — template same size as frame raises ValueError
    def test_template_same_size_as_frame_raises_error(self):
        # Save full frame as template — should be rejected
        full_template_path = os.path.join(self.temp_dir, "unittest_full_frame_template.png")
        cv2.imwrite(full_template_path, self.frame)

        with self.assertRaises(ValueError):
            self.matcher.match(self.frame, full_template_path)

    def tearDown(self):

        test_failed = False
        if hasattr(self, "_outcome"):
            result = self._outcome.result

            test_failed = (
                len(result.failures) > 0 or
                len(result.errors) > 0
            )

        if not test_failed:
            TempManager.delete_temp_subfolder("unit_tests_visual_match")

if __name__ == "__main__":
    unittest.main(verbosity=2)