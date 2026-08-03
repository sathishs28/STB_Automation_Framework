# analysis/ocr.py
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from core.logger import logging

# Log set
# setup_logging()

# Load .env
try:
    load_dotenv()
except Exception:
    pass

logger = logging.getLogger(__name__)

# Point pytesseract to the Tesseract binary
# Getting the tessract path from .env, if not exits. Used default path.
tesseract_path = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = tesseract_path

class OCREngine:

    def __init__(self):
        self._verify_tesseract()

    def _verify_tesseract(self):
        print(pytesseract.pytesseract.tesseract_cmd)
        """Fail fast if Tesseract is not installed."""
        if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            logger.error(f"❌ Tesseract not found at: {pytesseract.pytesseract.tesseract_cmd}")
            logger.error("   Check → TESSERACT_PATH in .env")
            raise EnvironmentError("Tesseract not installed or path is wrong")
        logger.info("✅ Tesseract found")

    def extract_text(self, frame, region=None):
        """
        Extract all text from a frame or region.

        frame  : numpy BGR array from grab_frame()
        region : (x, y, w, h) to read only part of screen
                 None = read full frame

        Returns: string of all detected text
        """
        # Crop to region if specified
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]

        # Preprocess for better OCR accuracy
        processed = self._preprocess(frame)

        # Run OCR
        text = pytesseract.image_to_string(processed, config="--psm 6")
        text = text.strip()

        logger.info(f"OCR extracted: '{text}'")
        return text

    def contains_text(self, frame, expected_text, region=None, case_sensitive=False):
        """
        Check if expected text appears on screen.

        Returns: (found, full_text)
        """
        full_text = self.extract_text(frame, region)

        if not case_sensitive:
            found = expected_text.lower() in full_text.lower()
        else:
            found = expected_text in full_text

        if found:
            logger.info(f"✅ Text found: '{expected_text}'")
        else:
            logger.warning(f"❌ Text not found: '{expected_text}' in '{full_text}'")

        return found, full_text

    def extract_text_blocks(self, frame, region=None):
        """
        Extract text with position data.
        Returns list of dicts with text, x, y, w, h, confidence.
        Useful for finding where specific text appears on screen.
        """
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]

        processed = self._preprocess(frame)

        data   = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        blocks = []

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])

            # Only include results with reasonable confidence
            if text and conf > 50:
                blocks.append({
                    "text"      : text,
                    "x"         : data["left"][i],
                    "y"         : data["top"][i],
                    "w"         : data["width"][i],
                    "h"         : data["height"][i],
                    "confidence": conf
                })

        logger.info(f"OCR found {len(blocks)} text blocks")
        return blocks

    def _preprocess(self, frame):
        """
        Improve OCR accuracy by preprocessing the frame.
        Grayscale + resize + threshold = cleaner text edges.
        """
        # Convert BGR to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Scale up — Tesseract works better on larger images
        scaled = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

        # Threshold — make text black on white background
        _, thresh = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        ### Debug purpose
        """
        # Save the processed images.
        cv2.imwrite('temp/processed_gray_image.png', gray)
        cv2.imwrite('temp/processed_scaled_image.png', scaled)
        """
        
        return thresh