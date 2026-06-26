# analysis/timing.py
import time
import numpy as np
import cv2
from core.logger import logging

logger = logging.getLogger(__name__)


class TimingEngine:

    def __init__(self):
        self._start_time = None

    # ── 1. Simple timer ───────────────────────────────────
    def start(self):
        """Start the timer."""
        self._start_time = time.perf_counter()
        logger.info("⏱ Timer started...")

    def stop(self):
        """
        Stop timer and return elapsed milliseconds.
        """
        elapsed_ms = 0
        if self._start_time is None:
            raise RuntimeError("Timer not started — call start() first")
        
        elapsed_ms       = (time.perf_counter() - self._start_time) * 1000
        self._start_time = None
        logger.info(f"⏱ Timer stopped — elapsed: {elapsed_ms:.1f}ms") 
        return elapsed_ms

    # ── 2. Zap time measurement ───────────────────────────
    # Need to modify... currently it's understanding purpose.
    def measure_zap_time(self, grab_frame_fn, send_key_fn,
                         key, detect_fn,
                         timeout=10, poll_interval=0.1):
        """
        Measure channel change time — from key press to new content appearing.

        grab_frame_fn  : callable → backend.grab_frame()
        send_key_fn    : callable → backend.send_key()
        key            : key to send e.g. "CH_UP"
        detect_fn      : callable(frame) → True when new channel is visible
                         e.g. lambda f: not av.is_black_screen(f)[0]
        timeout        : max seconds to wait for channel to appear
        poll_interval  : how often to check in seconds

        Returns: (success, elapsed_ms)
        """
        logger.info(f"Measuring zap time for key='{key}'")

        # Send key and start timer simultaneously
        send_key_fn(key)
        start = time.perf_counter()

        # Poll until detect_fn returns True or timeout
        deadline = start + timeout

        while time.perf_counter() < deadline:
            frame = grab_frame_fn()

            if detect_fn(frame):
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"✅ Channel appeared — zap time: {elapsed_ms:.1f}ms")
                return True, elapsed_ms

            time.sleep(poll_interval)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(f"❌ Channel did not appear within {timeout}s")
        return False, elapsed_ms

    # ── 3. Frame change detection ─────────────────────────
    # To Test and find the STB Crash/Hang issue
    def wait_for_frame_change(self, grab_frame_fn,
                              baseline_frame,
                              threshold=0.01,
                              timeout=10,
                              poll_interval=0.1):
        """
        Wait until the next frame changes significantly from baseline (intialy captured frame).
        Used to detect when the STB video stuck/hang 

        baseline_frame : frame captured at initialy
        threshold      : fraction of pixels that must change (0.01 = 1%)

        Returns: (changed, elapsed_ms, new_frame)
        """
        logger.info("Waiting for screen/frame change...")
        start    = time.perf_counter()
        deadline = start + timeout
        logger.debug(f"Printing the start time:{start} and deadline:{deadline}")

        baseline_gray = cv2.cvtColor(baseline_frame, cv2.COLOR_BGR2GRAY)
        
        while time.perf_counter() < deadline:
            frame      = grab_frame_fn()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Count pixels that changed significantly
            # Calculate the absolute difference between two arrays or between an array and a scalar value
            diff          = cv2.absdiff(baseline_gray, frame_gray)  
            changed_pixels = np.sum(diff > 30)
            change_ratio   = changed_pixels / diff.size

            if change_ratio >= threshold:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"✅ Screen/frame changed — {change_ratio*100:.1f}% pixels changed | {elapsed_ms:.1f}ms")
                return True, elapsed_ms, frame

            time.sleep(poll_interval)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(f"❌ No screen change detected within {timeout}s")
        return False, elapsed_ms, None

    # ── 4. Multi-zap benchmark ────────────────────────────
    def benchmark_zap(self, grab_frame_fn, send_key_fn,
                      key, detect_fn, repeat=5, wait_between=3):
        """
        Measure zap time multiple times and return statistics.
        Gives average, min, max — better than a single measurement.

        Returns: dict with avg, min, max, all_times, pass_count
        """
        logger.info(f"Benchmarking zap time — {repeat} runs")
        times      = []
        pass_count = 0

        for i in range(repeat):
            logger.info(f"Run {i+1}/{repeat}")
            success, elapsed = self.measure_zap_time(
                grab_frame_fn, send_key_fn, key, detect_fn
            )
            if success:
                times.append(elapsed)
                pass_count += 1

            # Wait for channel to settle before next zap
            time.sleep(wait_between)

        result = {
            "pass_count" : pass_count,
            "total_runs" : repeat,
            "avg_ms"     : round(sum(times) / len(times), 1) if times else None,
            "min_ms"     : round(min(times), 1) if times else None,
            "max_ms"     : round(max(times), 1) if times else None,
            "all_ms"     : [round(t, 1) for t in times]
        }

        logger.info(f"Benchmark result → avg={result['avg_ms']}ms | "
                    f"min={result['min_ms']}ms | max={result['max_ms']}ms")
        return result