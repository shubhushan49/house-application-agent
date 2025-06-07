from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
import multiprocessing as mp

class EvListener(AbstractEventListener):
    def __init__(self, lock, val):
        super().__init__()
        self.run = True
        self.lock = lock
        self.val = val
    
    def set_run_to_f(self):
        self.run = False

    def after_find(self, by, value, driver : webdriver.Chrome):
        """Check if the user has clicked stop in tkinter after finding an element"""
        print(f":::After Find:::Value of shared value is: {self.val.value}")
        with self.lock:
            if self.val.value:
                print("\t\t\tClosing the Driver")
                driver.close()
                driver.quit()
    
    def before_click(self, elem, driver: webdriver.Chrome):
        """Check if user has clicked stop in tkinter before clicking on an element"""
        print(f":::Before Click:::Value of shared value is: {self.val.value}")
        with self.lock:
            if self.val.value:
                print("\t\t\tClosing the Driver")
                driver.close()
                driver.quit()

    def after_click(self, elem, driver: webdriver.Chrome):
        """Check if user has clicked stop in tkinter before clicking on an element"""
        print(f":::Before Click:::Value of shared value is: {self.val.value}")
        with self.lock:
            if self.val.value:
                print("\t\t\tClosing the Driver")
                driver.close()
                driver.quit()