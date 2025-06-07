# selenium imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver

# other imports
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from utils.models import ENGINE, Base
from utils.sel_listener import EvListener

from tkinter import Tk, Button, Label, Text, Entry
from pathlib import Path
import multiprocessing as mp
import logging
import logging.handlers

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# relative imports
from utils.wg_gesucht import Wg_Workflow

# create  selenium driver
chrome_options = Options()
chrome_options.add_argument("--start-fullscreen")
# Global variables for inter process communication
LOCK = mp.Lock()
SHARED_VALUE = mp.Value('i', 0)


def selenium_process(
        lock,
        process_val,
        USERNAME,
        PASSWORD,
        WG_ZIMMER_INTRO,
        OTHER_INTRO,
        CITY,
        ):
    """
        lock: mp.Lock
        process_val: mp.Value
    """
    sel_driver = EventFiringWebDriver(webdriver.Chrome(options=chrome_options), EvListener(lock, process_val))

    room_types = [Wg_Workflow.WG_ZIMMER]

    wg = Wg_Workflow(
        username=USERNAME,
        password=PASSWORD,
        driver=sel_driver,
        cookies_path=Path(__file__).parent / "cookies.pkl",
        room_types=room_types,
        city=CITY,
        wg_intro=WG_ZIMMER_INTRO,
        other_intro=OTHER_INTRO
    )

    Base.metadata.create_all(ENGINE)

    wg.login()
    wg.search()
    wg.get_through_rooms()


class Window(Tk):
    def __init__(self):
        super().__init__()
        # self.manager = SelManager()
        # self.manager.start()
        # self.sharedListener = self.manager.EvListener()
        self.sharedListener = EvListener
        self.WG_ZIMMER_INTRO = None
        self.OTHER_INTRO = None
        self.CITY = None
        self.USERNAME = None
        self.PASSWORD = None
        self.driver = None
        self.DRIVER = None
        self.bot_process = None
        self.title("WG Gesucht Bot")

        if self.config_exists():
            self.run_bot_ui()
        else:
            self.homepage_ui()
    
    def config_exists(self):
        return Path(".env").exists()
    
    def homepage_ui(self):
        self.geometry("1400x800")
        # Username label and entry
        self.user_label = Label(self, text="Username")
        self.user_label.pack(pady=5)

        self.username = Entry(self)
        self.username.pack(pady=5)

        # Password label and entry
        self.password_label = Label(self, text="Password")
        self.password_label.pack(pady=5)

        self.password = Entry(self, show="*")
        self.password.pack(pady=5)

        # City
        self.city_label = Label(self, text="City")
        self.city_label.pack(pady=5)

        self.city = Entry(self)
        self.city.pack(pady=5)

        # wg intro
        self.wg_intro_label = Label(self, text = "WG Zimmer Intro")
        self.wg_intro_label.pack(pady=5)

        self.wg_intro_text = Text(self, width=100, height=10)
        self.wg_intro_text.pack(pady=5)
        # other intro
        self.other_intro_label = Label(self, text = "Other Intro")
        self.other_intro_label.pack(pady=5)

        self.other_intro_text = Text(self, width=100, height=10)
        self.other_intro_text.pack(pady=5)
        # Save button
        self.button = Button(self, text="Save Credentials")
        self.button.bind("<Button-1>", self.saveConfig)
        self.button.pack(pady=10)
    
    def run_bot_ui(self):
        self.geometry("800x400")
        self.run_button = Button(self, text="Run Bot")
        self.run_button.bind("<Button-1>", self.startBot)
        self.run_button.pack(pady=10)

        self.cancel_run_button = Button(self, text="Cancel Run")
        self.cancel_run_button.bind("<Button-1>", self.cancelRun)
        self.cancel_run_button.pack(pady=10)
    
    def cancelRun(self, event):
        print("*"*50)
        print("Canceling run")
        if self.bot_process and self.bot_process.is_alive():
            # self.sharedListener.set_run_to_f()
            with LOCK:
                SHARED_VALUE.value = 10
            print("Terminating bot process... sleeping for 20s")
            time.sleep(20)
            self.bot_process.terminate()
            self.bot_process.join()
            self.bot_process = None
            print("Bot process terminated successfully.")

    def saveConfig(self, event):
        self.USERNAME = self.username.get()
        self.PASSWORD = self.password.get()
        self.CITY = self.city.get()
        self.WG_ZIMMER_INTRO = self.wg_intro_text.get("1.0", "end-1c").replace('\n', '<nn>')
        self.OTHER_INTRO = self.other_intro_text.get("1.0", "end-1c").replace('\n', '<nn>')
        
        with open(".env", "w") as f:
            f.write(f"WG_GESUCHT_USERNAME=\"{self.USERNAME}\"\n")
            f.write(f"WG_GESUCHT_PASSWORD=\"{self.PASSWORD}\"\n")
            f.write(f"CITY=\"{self.CITY}\"\n")
            f.write(f"WG_ZIMMER_INTRO=\"{self.WG_ZIMMER_INTRO}\"\n")
            f.write(f"OTHER_INTRO=\"{self.OTHER_INTRO}\"\n")
        
        self.WG_ZIMMER_INTRO = self.WG_ZIMMER_INTRO.replace("<nn>", "\n")
        self.OTHER_INTRO = self.OTHER_INTRO.replace("<nn>", "\n")

        self.username.delete(0, 'end')
        self.password.delete(0, 'end')
        self.city.delete(0, 'end')
        self.wg_intro_text.delete("1.0", "end-1c")
        self.other_intro_text.delete("1.0", "end-1c")

        for widget in self.winfo_children():
            widget.destroy()

        self.run_bot_ui()
    
    def getConfig(self):
        self.USERNAME = os.getenv("WG_GESUCHT_USERNAME")
        self.PASSWORD = os.getenv("WG_GESUCHT_PASSWORD")
        self.CITY = os.getenv("CITY")
        self.WG_ZIMMER_INTRO = os.getenv("WG_ZIMMER_INTRO", "").replace("<nn>", "\n")
        self.OTHER_INTRO = os.getenv("OTHER_INTRO", "").replace("<nn>", "\n")
    
    def startBot(self, event):
        # self.manager.start()
        if not self.USERNAME:
            self.getConfig()
        if self.bot_process and self.bot_process.is_alive():
            print("Bot is already running!")
            return
        # start the process with a shared value of 0
        with LOCK:
            SHARED_VALUE.value = 0
        # self.bot_process = mp.Process(target=self.runBot, args=(self.stop_event,))
        self.bot_process = mp.Process(target=selenium_process, args=(LOCK, SHARED_VALUE, self.USERNAME, self.PASSWORD, self.WG_ZIMMER_INTRO, self.OTHER_INTRO, self.CITY,))
        self.bot_process.start()
    
    def runBot(self):
        self.driver = webdriver.Chrome(options=chrome_options)
        self.DRIVER = EventFiringWebDriver(self.driver, self.sharedListener)

        self.DRIVER.fullscreen_window()

        room_types = [Wg_Workflow.WG_ZIMMER]

        wg = Wg_Workflow(
            username=self.USERNAME,
            password=self.PASSWORD,
            driver=self.DRIVER,
            cookies_path=Path(__file__).parent / "cookies.pkl",
            room_types=room_types,
            city=self.CITY,
            wg_intro=self.WG_ZIMMER_INTRO,
            other_intro=self.OTHER_INTRO
        )

        Base.metadata.create_all(ENGINE)

        wg.login()
        wg.search()
        wg.get_through_rooms()

if __name__ == "__main__":
    window = Window()
    window.mainloop()