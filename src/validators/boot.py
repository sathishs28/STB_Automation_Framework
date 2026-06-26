# boot.py -- Boot related functions/methods.
import time
import cv2
from core.logger import logging
from pathlib import Path
from core.exceptions import CaptureError, ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)

class Boot:
    
    def __init__(self, customer, config, backend, matcher, ocr, av, timer):
        self.customer = customer
        self.config = config
        self.backend = backend
        self.matcher = matcher
        self.ocr = ocr
        self.av = av
        self.timer = timer

        self._timer_started = False
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.templates_path = (
        PROJECT_ROOT
            / "assets"
            / "customers"
            / self.customer
            / "templates"
        )

        self.evidence_path = (
            PROJECT_ROOT
            / "evidence"
        )
        logger.debug(f"Boot Module called, to check the {self.customer} Boot Test Cases")
    # To verify the HDMI input status    
    def hdmi_input_detect(self, timeout=30):
        """
        This method is used to detect the first frame.
        Checking the current frame is black or not. If it detect black frame until it wait upto timeout time.
        If the frame has content not black then return the status: True
        """
        for i in range(timeout,0,-1):
            frame = self.backend.grab_frame()
            _, percentage = self.av.is_black_screen(frame)
            if percentage == 100:
                logger.warning("No HDMI input")
            else:
                logger.info("HDMI Input detected")
                return True
            logger.info("Waiting for HDMI Input...")
            logger.info("⚠️ Timeout in %d sec", i)
            time.sleep(1)
                
        raise CaptureError("HDMI input not detected within timeout")     
    
    # Private method to check the full frame validation
    def __boot_logo_ad_check(self, index, template):
        """
        This is common method is used to match and check the full frame.
        That means live frame is same as template of Boot logo, ad, logo2, loading.
        Note:
            grab_frame_fn  -> Checking the every frame to match, if it changed we asume the next logo has came.
            baseline_frame -> First frame of the logo 
            threshold      -> Match threshold of frame (For more details refer - analysis/av_quality.py)
            timeout        -> Maximum wait time for the current logo frame checking. If it exceds test will raise - Failed.
        """
        # To verify the live Boot logo is identical to boot logo template
        frame = self.backend.grab_frame()
        template_path = f"{self.templates_path}/{template}"
        status, _ = self.matcher.is_same(frame, template_path)

        # Boot Logo/ad detect, then check the total duration of boot time.
        elapsed_time = 0
        if status:
            # Starting the timer in first interation only to find the total boot time
            if index == 0:
                self.timer.start()
                self._timer_started = True

            # Frame Change
            baseline = self.backend.grab_frame()
            _, elapsed_ms, _ = self.timer.wait_for_frame_change(
            grab_frame_fn  = self.backend.grab_frame,
            baseline_frame = baseline,
            threshold      = 0.01,
            timeout        = 60
            )
            elapsed_time = elapsed_ms / 1000

        else:
            logger.warning(f"{self.customer} {template} mistmatch")
            output_path = f"{self.evidence_path}/{self.customer}_'{template}'_mistmatch_{self.timestamp}.png"
            cv2.imwrite(output_path, frame)
            logger.info(f"Debug image saved → {output_path}")
        return status, elapsed_time
        
    # Bootup logo validation
    def is_boot_logo_present(self, index):
        logger.info("Verify the Boot logo is present")
        
        # Verify the first frame, to check the HDMI input
        self.hdmi_input_detect()
            
        # Boot Logo check
        return self.__boot_logo_ad_check(index, template=self.config.get("ui_templates.boot_logo"))
    
    # Bootup logo-2 Check
    def is_boot_logo2_present(self, index):
        logger.info("Verify the Boot logo2 is present")
        
        # Verify the first frame, to check the HDMI input
        self.hdmi_input_detect()
            
        # Boot Logo check
        return self.__boot_logo_ad_check(index, template="boot_logo2")
    
    # Bootup advertisment Check
    def is_boot_ad_present(self, index):
        logger.info("Verify the Boot ad is present")
        
        # Verify the first frame, to check the HDMI input
        self.hdmi_input_detect()
            
        # Boot ad check
        return self.__boot_logo_ad_check(index, template=self.config.get("ui_templates.boot_ad"))
    
    # Bootup image - loading... Check
    def is_loading_present(self):
        pass
    
    def check_boot_sequence(self):

        boot_sequence = self.config.get("boot_sequence")
        if not boot_sequence:
            raise ConfigError("boot_sequence not defined in customer config")
        
        try:
            if len(boot_sequence) >= 1:
                logger.info(f"Customer:{self.customer} Boot Sequence loaded")
                logger.info(f"Boot Sequence:{boot_sequence}")

                boot_steps = {
                "boot_logo": self.is_boot_logo_present,
                "boot_logo2": self.is_boot_logo2_present,
                "boot_ad": self.is_boot_ad_present,
                "boot_loading": self.is_loading_present,
                }

                results = {}
                total_elapsed_time = 0
                for index, step in enumerate(boot_sequence):
                    method = boot_steps.get(step)
                    
                    # Checking the each boot sequence in customer config, if not there skiped that method.
                    if method is None:
                        logger.warning("Unknown boot sequence step: %s", step)
                        continue

                    logger.info("Executing boot step: %s", step)

                    # Excuting the boot sequence here...
                    status, elapsed_time = method(index)
                    results[step] = {
                        "status": status,
                        "elapsed_time": elapsed_time
                    }
                    
                    # Stoped the timer - End of the boot step.
                    if index == len(boot_sequence) - 1 and self._timer_started:
                       total_elapsed_time = self.timer.stop()
                       self._timer_started = False
                       total_elapsed_time = round(total_elapsed_time / 1000)
                    logger.debug("Total Boot time: %d", total_elapsed_time)
                    if not status:
                        logger.error("Boot sequence failed at step: %s", step)
                        return False, total_elapsed_time, results
                    
                # Verify the total boot time (STB should boot within )
                if total_elapsed_time <= self.config.get("timeouts.boot_to_live"):
                    logger.info(f"Total Boot time: {total_elapsed_time}")
                    return True, total_elapsed_time, results
                else:
                    max_boot = self.config.get("timeouts.boot_to_live")
                    logger.info(f"Current Boot time: {total_elapsed_time}s exceeded max {max_boot}s")
                    return False, total_elapsed_time, results
                
        except ConfigError as e :
            logger.error("Boot sequence is not loaded", e) 
            raise ConfigError("Boot sequence is not loaded")       
          
    def af_boot_is_live_tv_playing(self):
        pass

    def check_boot_time(self):
        pass

    def boot_ad_bypass(self):
        pass