# analysis/visual_match.py
from tempfile import template

import cv2
import numpy as np
import logging
import os
from core.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class VisualMatcher:

    def __init__(self, threshold=0.85):
        """
        threshold : match confidence 0.0 to 1.0
                    0.85 = 85% similar — good default
                    higher = stricter match
        """
        self.threshold = threshold

    def match(self, frame, template_path):
        """
        Check if template image exists in the live frame.

        frame         : numpy array from grab_frame() — full screen
        template_path : path to small reference image

        Returns: (found, score, location)
          found    : True / False
          score    : 0.0 to 1.0 confidence
          location : (x, y, w, h) where found, or None
        """
        # Load template
        if not os.path.exists(template_path):
            logger.error(f"❌ Template not found: {template_path}")
            raise FileNotFoundError(f"Template not found: {template_path}")

        template = cv2.imread(template_path)    # Read the template image from the specified path
        if template is None:
            raise ValueError(f"❌ Could not read template: {template_path}")

        # Convert both to grayscale — more reliable matching
        frame_gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        """
        th = template_gray.shape[0]  # height of the template
        tw = template_gray.shape[1]  # width of the template
        fh = frame_gray.shape[0]     # height of the frame
        fw = frame_gray.shape[1]     # width of the frame    
        """
        th, tw = template_gray.shape[:2]
        fh, fw = frame_gray.shape[:2]
        logger.info(f"Template size: {tw}x{th} | Frame size: {fw}x{fh}")
        # ✅ Guard — template must be smaller than frame
        if tw >= fw or th >= fh:
            logger.error(f"❌ Template ({tw}x{th}) must be smaller than frame ({fw}x{fh})")
            raise ValueError("Template must be smaller than the frame")

        # ✅ Guard — template too small gives unreliable results
        if tw < 10 or th < 10:
            logger.warning(f"⚠️ Template very small ({tw}x{th}) — results may be unreliable")

        # Reject featureless templates
        if np.std(template_gray) < 1:
            raise ValueError(
                "Template contains insufficient visual features"
            )
        # Run template matching
        result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        # Get best match score and location
        _, score, _, location = cv2.minMaxLoc(result)
        logger.info(f"Match score: {score:.4f}")
        logger.info(f"Match location: {location}")

        """ This is the debug purpose, Do not use """
        """
        x, y = location
        h, w = template.shape[:2]

        matched = frame[y:y+h, x:x+w]

        cv2.imwrite("matched_area.png", matched)
        cv2.imwrite("template.png", template)

        debug = frame.copy()

        cv2.rectangle(
            debug,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )
        cv2.imwrite("debug_location.png", debug)
        """

        found = score >= self.threshold

        if found:
            x, y   = location
            logger.info(f"✅ Template matched — score={score:.2f} | location=({x},{y})")
            return True, score, (x, y, tw, th)
        else:
            logger.warning(f"❌ Template not matched — score={score:.2f} < threshold={self.threshold}")
            return False, score, None

    def match_region(self, frame, template_path, region):
        """
        Match template only within a specific screen region.
        Faster than full-screen search.

        region : (x, y, w, h) — area to search within
        """
        x, y, w, h = region
        cropped     = frame[y:y+h, x:x+w]
        return self.match(cropped, template_path)

    def save_debug_image(self, frame, template_path, output_path):
        """
        Save a debug image showing where the template was found.
        Useful for investigating failed tests.
        """
        found, score, location = self.match(frame, template_path)

        debug_frame = frame.copy()

        if found:
            x, y, w, h = location
            # Draw green rectangle around match
            cv2.rectangle(debug_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(debug_frame, f"Match: {score:.2f}",
                       (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            # Draw red text — not found
            cv2.putText(debug_frame, f"No match: {score:.2f}",
                       (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        cv2.imwrite(output_path, debug_frame)
        logger.info(f"Debug image saved → {output_path}")

        return found, score, location
    
    def is_same(self, frame, template_path):
        """
        Identify the frame1 -> Live frame and frame2 -> full frame template are equal/same.
        To use this method for boot logo,ad and other full frame epg, stb info..etc. are present or not.
        
        """
        try:
            # Check whether the template file exists
            if not os.path.exists(template_path):
                logger.error(f"❌ Template not found: {template_path}")    
                raise FileNotFoundError(f"Template not found: {template_path}")
            
            # Load template image
            template = cv2.imread(template_path)    # Read the template image from the specified path
            
            if template is None:
                raise FileNotFoundError(f"Failed to read template image: {template_path}")
            
            logger.info(f"✅ Template loaded successfully: {template_path}")
        
        except FileNotFoundError:
            logger.exception(f"⚠️ Template file not found: {template_path}")
            raise

        except Exception:
            logger.exception(f"❌ Failed to load template: {template_path}")
            raise

        result = cv2.matchTemplate(
            frame,
            template,
            cv2.TM_CCOEFF_NORMED
        )
        
        _, max_val, _, _ = cv2.minMaxLoc(result)

        logger.info(f"Identical Match Score: {max_val:.4f}")

        if max_val >= 0.95:
            logger.info(" ✅ Template Frame detected")
            return True, max_val
        else:
            logger.warning("❌ Template Frame is not detected")
            return False, None