import time

import cv2
from core.logger import logging
from src.remote import Remote
from ast import literal_eval

logger = logging.getLogger(__name__)


class Menu:

    def __init__(self, ctx):
        self.ctx = ctx

        # Initialize the Remote class with the backend
        self.remote = Remote(self.ctx)

    def invoke_menu(self, repeat=3):

        for _ in range(repeat):
            self.remote.menu(delay=1)
            menu_frame = self.ctx.backend.grab_frame()
            menu_template_path = f"{self.ctx.templates_path}/{self.ctx.config.get('ui_templates.menu')}"
            menu_found, _, _ = self.ctx.matcher.match(menu_frame, menu_template_path)

            if menu_found:
                logger.info("Menu Screen Invoked ✅")
                return True
            else:
                logger.info("Menu Screen Not Invoked, retrying... ")
            time.sleep(3)
        logger.warning("Menu Screen Not Invoked ❌")
        return False

    def go_to_autosearch(self):
        # Get the autosearch navigate key sets
        search_key = self.ctx.config.get("navigate.auto_search")
        logger.info(type(search_key))
        logger.info(f"navigate keys: {search_key}")
        """ Partially implemented, will do later """