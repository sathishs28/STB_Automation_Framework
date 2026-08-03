import time

import cv2
from core.logger import logging
from src.navigators import menu
from src.remote import Remote
from src.navigators.menu import Menu

logger = logging.getLogger(__name__)


class Autoscan:

    def __init__(self, ctx):
        self.ctx = ctx
        
        # Initialize the Remote class with setup context
        self.remote = Remote(self.ctx)

        # Initialize the Menu Class with setup context
        self.menu = Menu(self.ctx)


    def go_to_autoscan(self, wait_time=10):
        """
        This method is used to navigate to the autoscan menu.
        """
        if self.menu.invoke_menu() and self.menu.go_to_autosearch():
            logger.info("Autoscan menu navigation started.")
        else:
            logger.warning("Failed to navigate to autoscan menu.")

        logger.info("Autoscan menu navigation complete.")

        menu_frame = self.ctx.backend.grab_frame()
        menu_template_path = f"{self.ctx.templates_path}/{self.ctx.config.get('ui_templates.menu')}"
        menu_found, _ , _ = self.ctx.matcher.match(menu_frame, menu_template_path)
        
        if menu_found:
            logger.info("Menu screen detected. Navigating to Autoscan...")
            self.ctx.remote.right()
            time.sleep(1)
            self.ctx.remote.ok()

            pwd_frame = self.ctx.backend.grab_frame()
            pwd_template_path = f"{self.ctx.templates_path}/{self.ctx.config.get('ui_templates.password')}"
            pwd_found, _ , _ = self.ctx.matcher.match(pwd_frame, pwd_template_path)

            if pwd_found:
                logger.info("Password screen detected. Entering password...")
                password = ["0", "0", "0", "0"]  # Example password sequence
                
                self.ctx.remote.send_key_sequence(password)
                
                for _ in range(wait_time):
                    auto_search_frame = self.ctx.backend.grab_frame()
                    found, _ = self.ctx.ocr.contains_text(auto_search_frame, "Auto Search")
                                
                    if found:
                        logger.info("Auto Search screen detected.")
                        return True
                    else:
                        logger.info("Waiting for Auto Search screen...")
                        time.sleep(0.5)
                logger.error("Auto Search screen not detected after entering password.")
                return False
        return None

    def is_autoscan_failed(self, delay=15, repeat=1):
        """
        This method is used to check if the autoscan process has failed.
        param timeout The maximum time to wait for the autoscan to complete.
        """
        interation = 1
        while True:
            logger.info("Checking if Autoscan has failed...")
            for _ in range(repeat):
                # logger.info(f" ✅✅✅ Autoscan Check attempt: {attempt + 1} ✅✅✅ ")
                logger.info(f" ✅✅✅ Autoscan Check attempt: {interation} ✅✅✅ ")
                auto_scan = self.ctx.go_to_autoscan()

                if auto_scan:
                    # self.ctx.timer.start()
                    tune_started = False
                    while True:
                        auto_search_frame = self.ctx.backend.grab_frame()
                        found_autoscan, _ = self.ctx.ocr.contains_text(auto_search_frame, "Auto Search")
                        
                        if found_autoscan:
                            logger.info("Autoscan in progress. Waiting for completion...") 
                        
                        else:
                            logger.info("Auto scan exited or completed.")
                            tune_started = False  # Reset the tune_started flag for the next attempt
                            break  # Exit the while loop if "Auto Search" is not found
                            
                        if not tune_started:
                            # Check weathere the tuning is started or not by looking for the "Tune percentage" text in the specified region
                            tune_percentage_region = (1026, 552, 81, 53)  # region for "Tune percentage"
                            tune_found, text = self.ctx.ocr.contains_text(auto_search_frame, "0%", region=tune_percentage_region)
                            logger.info(f"Tuning percentage: {text}")

                            if tune_found:
                                error_found, _ = self.ctx.ocr.contains_text(auto_search_frame, "Network information is not detected")
                            
                                if error_found:
                                    # logger.error(f"'Network information is not detected!' Error found at {attempt + 1}/{repeat}")
                                    logger.error(f"'Network information is not detected!' Error found at {interation}")
                                    output_path = f"{self.ctx.evidence_path}/{self.ctx.customer}_auto_scan_error_at_attempt_{interation}_{self.ctx.timestamp}.png"
                                    cv2.imwrite(output_path, auto_search_frame)
                                    logger.info(f"Error image saved → {output_path}")
                                    
                            else:
                                logger.info("Tuning has started. Waiting for completion...")
                                tune_started = True      

                else:
                    logger.error(f"Failed to navigate to Autoscan at {interation} attempt.")
                    output_path = f"{self.ctx.evidence_path}/{self.ctx.customer}_auto_scan_navigation_error_at_attempt_{interation}_{self.ctx.timestamp}.png"
                    cv2.imwrite(output_path, self.ctx.backend.grab_frame())
                    logger.info(f"Navigation error image saved → {output_path}")
                    
        
                if repeat > 1:
                    self.ctx.remote.exit(repeat=3)
                    logger.info("Wait for next try...")
                    time.sleep(delay)        
            
            interation += 1
            logger.info("Wait for next try...")
            self.ctx.remote.exit(repeat=3)
            time.sleep(delay)
            self.ctx.remote.exit(repeat=3)