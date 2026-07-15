import time
from core.logger import logging

logger = logging.getLogger(__name__)

class Remote:
    
    def __init__(self, ctx):    
        self.ctx = ctx
        self.backend = self.ctx.backend
        
    def send_key(self, key, repeat=1, delay=0.5):
        """
        This method is used to send a key press to the backend.
        :param key: The key to be sent.
        :param repeat: The number of times the key should be sent.
        :param delay: The delay between key presses.
        """
        logger.info(f"Sending key: {key} (repeat: {repeat})")
        for _ in range(repeat):
            self.backend.send_key(key)
            if delay > 0:
                time.sleep(delay)  # Small delay between key presses 

    def send_key_sequence(self, key_sequence):
        """
        This method is used to send a sequence of key presses to the backend.
        :param key_sequence: A list of keys to be sent in order.
        """
        logger.info(f"Sending key sequence: {key_sequence}")
        for key in key_sequence:
            self.send_key(key)

    def ok(self, repeat=1, delay=0.5):
        self.send_key("OK", repeat, delay=delay)

    def up(self, repeat=1, delay=0.5):
        self.send_key("UP", repeat, delay=delay)

    def down(self, repeat=1, delay=0.5):
        self.send_key("DOWN", repeat, delay=delay)

    def left(self, repeat=1, delay=0.5):
        self.send_key("LEFT", repeat, delay=delay)

    def right(self, repeat=1, delay=0.5):
        self.send_key("RIGHT", repeat, delay=delay)

    def menu(self, repeat=1, delay=0.5):
        self.send_key("MENU", repeat, delay=delay)

    def exit(self, repeat=1, delay=0.5):
        self.send_key("EXIT", repeat, delay=delay)

    def back(self, repeat=1, delay=0.5):
        self.send_key("BACK", repeat, delay=delay)

    def num0(self, repeat=1, delay=0.5):
        self.send_key("0", repeat, delay=delay)