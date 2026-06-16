# tests/unit_tests/unittest_ocr.py
import unittest
import numpy as np
import cv2
import os
from unittest.mock import patch
from analysis.ocr import OCREngine


class Test_OCREngine(unittest.TestCase):

    def setUp(self):
        self.ocr = OCREngine()

        # Create a test frame with white background
        self.frame = np.ones((720, 1280, 3), dtype=np.uint8) * 255

        # Write "BBC ONE" text onto the frame
        cv2.putText(
            self.frame, "BBC ONE",
            (100, 100), cv2.FONT_HERSHEY_SIMPLEX,
            2.0, (0, 0, 0), 3
        )

    # Test 1 — extract_text returns a string
    def test_extract_text_returns_string(self):
        text = self.ocr.extract_text(self.frame)
        self.assertIsInstance(text, str)

    # Test 2 — contains_text finds expected text
    def test_contains_text_found(self):
        found, _ = self.ocr.contains_text(self.frame, "BBC")
        self.assertTrue(found)

    # Test 3 — contains_text case insensitive
    def test_contains_text_case_insensitive(self):
        found, _ = self.ocr.contains_text(self.frame, "bbc one")
        self.assertTrue(found)

    # Test 4 — contains_text returns False for missing text
    def test_contains_text_not_found(self):
        found, _ = self.ocr.contains_text(self.frame, "ITV")
        self.assertFalse(found)

    # Test 5 — region extraction works
    def test_extract_text_region(self):
        region = (0, 0, 500, 200)
        text   = self.ocr.extract_text(self.frame, region=region)
        self.assertIsInstance(text, str)

    # Test 6 — wrong tesseract path raises EnvironmentError
    # This directly changes the value checked by
    @patch("analysis.ocr.pytesseract.pytesseract.tesseract_cmd",
       "C:/wrong/path/tesseract.exe")
    def test_wrong_tesseract_path_raises_error(self):
        with self.assertRaises(EnvironmentError):
            OCREngine()


if __name__ == "__main__":
    unittest.main(verbosity=2)