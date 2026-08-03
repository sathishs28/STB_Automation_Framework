# boot.py -- Boot related functions/methods.
import time
import cv2
from core.logger import logging
from core.exceptions import CaptureError, ConfigError
from src.validators.live_tv import LiveTV

logger = logging.getLogger(__name__)

class Boot:
    
    def __init__(self, ctx):
        self.ctx = ctx
        logger.debug(f"Boot Module called, to check the {self.ctx.customer} Boot Test Cases")

    # To verify the HDMI input status
    def hdmi_input_detect(self, timeout=30):
        """
        This method is used to detect the first frame.
        Checking the current frame is black or not. If it detects black frame until it wait upto timeout time.
        If the frame has content not black then return the status: True
        """
        for i in range(timeout,0,-1):
            frame = self.ctx.backend.grab_frame()
            _, percentage = self.ctx.av.is_black_screen(frame)
            if percentage == 100:
                logger.warning("No HDMI input")
            else:
                logger.info("HDMI Input detected")
                return True
            logger.info("Waiting for HDMI Input...")
            logger.info("⚠️ Timeout in %d sec", i)
            time.sleep(1)
             
        raise CaptureError("HDMI input not detected within timeout, "
                           "Check the STB output / capture card input Status...!")
    
    # Private method to check the full frame validation
    def __boot_logo_ad_check(self, index, template):
        """
        This is common method is used to match and check the full frame.
        That means live frame is same as template of Boot logo, ad, logo2, loading.
        Note:
            grab_frame_fn  -> Checking the every frame to match, if it changed we assume the next logo has came.
            baseline_frame -> First frame of the logo 
            threshold      -> Match threshold of frame (For more details refer - analysis/av_quality.py)
            timeout        -> Maximum wait time for the current logo frame checking. If it exceeds test will raise - Failed.
        """
        # To verify the live Boot logo is identical to boot logo template
        frame = self.ctx.backend.grab_frame()
        template_path = f"{self.ctx.templates_path}/{template}"
        status, _ = self.ctx.matcher.is_same(frame, template_path)

        # Boot Logo/ad detect, then check the total duration of boot time.
        elapsed_time = 0
        if status:
            # Starting the timer in first interation only to find the total boot time
            if index == 0:
                self.ctx.timer.start()
                self.ctx._timer_started = True

            # Frame Change
            baseline = self.ctx.backend.grab_frame()
            _, elapsed_ms, _ = self.ctx.timer.wait_for_frame_change(
            grab_frame_fn  = self.ctx.backend.grab_frame,
            baseline_frame = baseline,
            threshold      = 0.01,
            timeout        = 60
            )
            elapsed_time = elapsed_ms / 1000

        else:
            logger.warning(f"{self.ctx.customer} {template} mismatch")
            output_path = f"{self.ctx.evidence_path}/{self.ctx.customer}_'{template}'_mismatch_{self.ctx.timestamp}.png"
            cv2.imwrite(output_path, frame)
            logger.info(f"Debug image saved → {output_path}")
        return status, elapsed_time
        
    # Bootup logo validation
    def is_boot_logo_present(self, index):
        logger.info("Verify the Boot logo is present")
        
        # Verify the first frame, to check the HDMI input
        self.hdmi_input_detect()
            
        # Boot Logo check
        return self.__boot_logo_ad_check(index, template=self.ctx.config.get("ui_templates.boot_logo"))
    
    # Bootup logo-2 Check
    def is_boot_logo2_present(self, index):
        logger.info("Verify the Boot logo2 is present")
        
        # Verify the first frame, to check the HDMI input
        self.hdmi_input_detect()
            
        # Boot Logo check
        return self.__boot_logo_ad_check(index, template="boot_logo2")
    
    # Bootup advertisement Check
    def is_boot_ad_present(self, index):
        logger.info("Verify the Boot ad is present")
        
        # Verify the first frame, to check the HDMI input
        self.hdmi_input_detect()
            
        # Boot ad check
        return self.__boot_logo_ad_check(index, template=self.ctx.config.get("ui_templates.boot_ad"))
    
    # Bootup image - loading... Check
    def is_loading_present(self):
        pass
    
    def check_boot_sequence(self):

        boot_sequence = self.ctx.config.get("boot_sequence")
        if not boot_sequence:
            raise ConfigError("boot_sequence not defined in customer config")
        
        try:
            if len(boot_sequence) >= 1:
                logger.info(f"Customer:{self.ctx.customer} Boot Sequence loaded")
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
                    
                    # Checking the boot sequence in customer config, if not there skipped that method.
                    if method is None:
                        logger.warning("Unknown boot sequence step: %s", step)
                        continue

                    logger.info("Executing boot step: %s", step)

                    # Executing the boot sequence here...
                    status, elapsed_time = method(index)
                    results[step] = {
                        "status": status,
                        "elapsed_time": elapsed_time
                    }
                    
                    # Stoped the timer - End of the boot step.
                    if index == len(boot_sequence) - 1 and self.ctx._timer_started:
                       total_elapsed_time = self.ctx.timer.stop()
                       self.ctx._timer_started = False
                       total_elapsed_time = round(total_elapsed_time / 1000)
                    logger.debug("Total Boot time: %d", total_elapsed_time)
                    if not status:
                        logger.error("Boot sequence failed at step: %s", step)
                        return False, total_elapsed_time, results
                    
                # Verify the total boot time (STB should boot within )
                if total_elapsed_time <= self.ctx.config.get("timeouts.boot_to_live"):
                    logger.info(f"Total Boot time: {total_elapsed_time}")
                    return True, total_elapsed_time, results
                else:
                    max_boot = self.ctx.config.get("timeouts.boot_to_live")
                    logger.info(f"Current Boot time: {total_elapsed_time}s exceeded max {max_boot}s")
                    return False, total_elapsed_time, results
           
        except ConfigError:
            logger.exception("Boot sequence is not loaded")
            raise
          
    def af_boot_is_live_tv_playing(self):
        """
        To confirm the live TV is playing, following validations called.
            HDMI Signal Present
                ▼ Yes - Continuous further validation | No (Raising Error)
            Black Screen Check
                ▼ Yes - Return status - False with reason | No - Continuous next validation
            If Video is freeze, check OCR text find (No Signal / Scrambled)
                ▼ Yes - Either no signal or scrambled i-frame. Service switch to LCN 999 and check the Live TV
                    No - Trying to service switch other service / Info service - LCN 999. Even after service switch Live TV is not playing meansing
                    Return - False with reason 
            Frame Motion Check (SSIM or Optical Flow)
                ▼ Yes - Return status - True | No - Checking the reason of failure.
            Audio Present?
                ▼ Yes Return - True (Live TV Playing) | No - Return - False with Reason
        """
        logger.info("To use detect the Live TV AV is playing or not")
        
        # Checking the HDMI input status, if Ture continuous further process.
        if self.ctx.hdmi_input_detect():

            ltv = LiveTV(self.ctx.customer, self.ctx.config, self.ctx.backend, self.ctx.matcher, self.ctx.ocr, self.ctx.av, self.ctx.timer)
            
            # Checking the current frame is black or not. If it detect black frame until it wait upto timeout time.
            if ltv.is_live_tv_playing():
                logger.info("Live TV is playing")
                return True, "Live TV is playing"
        