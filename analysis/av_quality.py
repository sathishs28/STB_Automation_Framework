# analysis/av_quality.py
import cv2
import time
import numpy as np
from core.logger import logging
from analysis.ocr import OCREngine
from skimage.metrics import structural_similarity as ssim
from pathlib import Path

logger = logging.getLogger(__name__)
ocr = OCREngine()

class AVQualityChecker:

    def __init__(self):
        # Each pixels brightness below this = black
        """ 
        For the grayscale frame in pixel color range 0 to 255.
        In this case, blank screen not exact 0.Due to the color filter, 
        capture device or stb middleware has some noise.
        """
        self.black_threshold  = 30
        self.black_percentage = 0.80  # 80% black pixels = black screen for 80 
        self.freeze_threshold = 0.995 # frames 99.5% similar = frozen

    # ── 1. Black screen detection ─────────────────────────

    def is_black_screen(self, frame, region=None):
        """
        Check if screen is black — no signal or STB crashed.

        Returns: (is_black, black_pixel_percentage)
        """
        # To check only the specified Region.
        if region:
            x, y, w, h = region
            frame = frame[y:y + h, x:x + w]

        # Convert the frame from color RGB to grayscale
        gray         = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite("temp/av_quality_gray_converted_image.png", gray)
        
        logger.debug(f"Minimum color value (0-255): {gray.min()}")
        logger.debug(f"Maximum color value (0-255): {gray.max()}")
        logger.debug(f"Meaning/accurate color value: {gray.mean():.2f}")
        
        black_pixels = np.sum(gray < self.black_threshold)
        logger.info(f"Total black/dark pixels in current frame: {black_pixels}")

        total_pixels = gray.size
        black_ratio   = black_pixels / total_pixels
   
        is_black = black_ratio >= self.black_percentage
        percentage = (black_ratio*100)
        
        if is_black:
            logger.warning(f"⚠️  Black screen detected — {percentage:.2f}% black pixels")
        else:
            logger.info(f"✅ Screen has content — {percentage:2f}% black pixels")
        return is_black, percentage

    # ── 2. Freeze / Motion detection ───────────────────────────────
    def is_frozen(self, frame1, frame2, freeze_threshold=5.0, region=None):
        """
        Compare two frames — if nearly identical, video is frozen.
        Grab two frames ~1 second apart and pass both here.

        Returns: (is_frozen, similarity_score)
        """
        # To check only the specified Region.
        if region:
            x, y, w, h = region
            frame1 = frame1[y:y + h, x:x + w]
            frame2 = frame2[y:y + h, x:x + w]

        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        score = np.mean(diff)
        is_frozen = score < freeze_threshold

        if is_frozen:
            logger.warning(f"⚠️ Frozen frame detected — similarity={score:.4f}")
            cv2.imwrite(f"evidence/{self}_frozen_frame1.png", frame1)
            cv2.imwrite(f"evidence/{self}_frozen_frame2.png", frame2)
        else:
            logger.info(f"✅ Video is moving — similarity={score:.4f}")
        return is_frozen, score

    def check_freeze_over_time(self, grab_frame_fn, duration=3, interval=1):
        """
        Monitor for freeze over a time window.
        Grabs frames at intervals and compares consecutive pairs.

        grab_frame_fn : callable — backend.grab_frame()
        duration      : total seconds to monitor
        interval      : seconds between grabs

        Returns: (is_frozen, details)
        """
        frames  = []
        samples = int(duration / interval)

        logger.info(f"Monitoring for freeze — {duration}s window, {samples} samples")

        for i in range(samples):
            frames.append(grab_frame_fn())
            if i < samples - 1:
                time.sleep(interval)

        # Compare each consecutive pair
        frozen_pairs = 0
        for i in range(len(frames) - 1):
            is_frozen, _ = self.is_frozen(frames[i], frames[i+1])
            if is_frozen:
                frozen_pairs += 1

        is_frozen = frozen_pairs >= (len(frames) - 1)

        if is_frozen:
            logger.warning(f"⚠️ Video frozen for entire {duration}s window")
        else:
            logger.info(f"✅ Video moving — {frozen_pairs}/{len(frames)-1} frozen pairs")

        return is_frozen, {"frozen_pairs": frozen_pairs, "total_pairs": len(frames) - 1}

    # ── 3. No signal detection ────────────────────────────

    def is_no_signal(self, frame1, frame2):
        """
        To Detect 'No Signal' screen — Combines black screen check, freeze, and No signal text.
        Returns: (no_signal, reason)
        """
        no_signal_txt_list = ["No signal", "No or Poor Cable Signal", "No Cable Signal", "Poor Cable Signal"]
        # Check 1 — Grab the frame and check the no signal text.
        
        for text in no_signal_txt_list:
            print("Printing the no signal list:", text)
            found, _ = ocr.contains_text(frame1, text)
            logger.debug(f"No signal found - {found}")
            if found:
                logger.warning(f"⚠️ No signal text found {text}")
                break
             
        # Check 2 — Verify the video frame is frozen.
        is_freeze, _ = self.is_frozen(frame1, frame2)
        logger.debug(f"Video freeze: {is_freeze}")

        if found and is_freeze:
            logger.warning("⚠️ No signal banner/i-frame is present")
            return True, "No signal"
        
        elif found and not is_freeze:
            logger.warning("⚠️ No signal banner is present, But background AV is playing...⚠️")
            return False, "No signal banner with AV playing"
        
        elif not found and is_freeze:
            logger.warning("⚠️ Video frozen, But No signal banner is not there ⚠️")
            return False, "Video stuck, There is no signal banner"
        
        else:
            logger.info("✅ AV is playing normally...✅")
            return False, "AV is playing"
        
    # ── 4. Combined health check ──────────────────────────

    def check_video_health(self, frame1, frame2=None):
        """
        Run all checks in one call.
        Pass two frames captured ~1s apart for freeze detection.

        Returns: dict with all check results
        """
        no_signal, _  = self.is_no_signal(frame1, frame2)
        is_black, black_pct = self.is_black_screen(frame1)

        result = {
            "no_signal"   : no_signal,
            "black_screen": is_black,
            "black_pct"   : round(black_pct * 100, 1),
            "frozen"      : False,
            "healthy"     : not no_signal and not is_black
        }

        # Freeze check needs two frames
        if frame2 is not None:
            is_frozen, score    = self.is_frozen(frame1, frame2)
            result["frozen"]    = is_frozen
            result["healthy"]   = result["healthy"] and not is_frozen
            result["freeze_score"] = round(score, 4)

        if result["healthy"]:
            logger.info("✅ Video health: OK")
        else:
            logger.warning(f"⚠️ Video health: FAIL → {result}")

        return result
    
    def is_frozen_ssim(self,frame1, frame2, region=None):

        """
        SSIM (Structural Similarity Index Measure) is a perceptual metric used to quantify 
        the degradation of image quality or compare similarities between two images
        """
        # To check only the specified Region.
        if region:
            x, y, w, h = region
            frame1 = frame1[y:y + h, x:x + w]
            frame2 = frame2[y:y + h, x:x + w]

        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        score, _ = ssim(gray1, gray2, full=True)
        is_frozen_ssim = score >= self.freeze_threshold

        if is_frozen_ssim:
            logger.warning(f"⚠️ Frozen frame detected By SSIM — similarity={score:.4f}")
        else:
            logger.info(f"✅ Video is moving — Detected By SSIM. Similarity={score:.4f}")
        return is_frozen_ssim, score

    def motion_detect(self, previous_frame, current_frame, threshold=5.0, region=None):
        """
        Detect motion between two frames.
        Args:
            previous_frame (numpy.ndarray)
            current_frame (numpy.ndarray)
            threshold (float): Mean pixel difference threshold.
            region (tuple): (x, y, w, h)
        Returns:
            bool
        """
        if previous_frame is None or current_frame is None:
            return False

        # Optional ROI to check only the specified Region.
        if region:
            x, y, w, h = region
            previous_frame = previous_frame[y:y + h, x:x + w]
            current_frame = current_frame[y:y + h, x:x + w]

        gray1 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        motion_score = np.mean(diff)
        status = motion_score > threshold

        if status:
            logger.info(f"✅ Video is moving. Motion Score={motion_score:.4f}")
        else:
            logger.warning(f"⚠️ Frozen frame detected, Motion Score={motion_score:.4f}")
        return status, motion_score

