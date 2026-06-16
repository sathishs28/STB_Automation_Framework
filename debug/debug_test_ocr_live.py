# test_ocr_live.py
from core.device_manager import Device_Manager
from analysis.ocr import OCREngine
from core.logger import logging 


logger = logging.getLogger(__name__)

dm      = Device_Manager()
backend = dm.startup()

frame = backend.grab_frame()
ocr   = OCREngine()

# Test 1 — extract all text from full screen
text = ocr.extract_text(frame)
print("Full screen text:")
print(text)
print("-" * 40)

# Test 2 — check if specific text is present
find = "dB"
found, full_text = ocr.contains_text(frame, find)
print(f"'{find}' found: {found}")

# Test 3 — read only a region (e.g. top banner area)
region = (0, 0, 1280, 720)   # top strip
text   = ocr.extract_text(frame, region=region)
print(f"Top region text: '{text}'")

# Test 4 — get text with positions
blocks = ocr.extract_text_blocks(frame)
for block in blocks:
    print(f"  '{block['text']}' at ({block['x']},{block['y']}) conf={block['confidence']}")

dm.shutdown()