# selenium imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# langchain imports
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import Agent, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool


# other imports
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from utils.models import ENGINE, Base

from tkinter import Tk, Button, Label, Text, Entry
from pathlib import Path
import multiprocessing

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from utils.config import WG_ZIMMER_INTRO, OTHER_INTRO, CITY

# relative imports
from utils.wg_gesucht import Wg_Workflow

# create  selenium driver
chrome_options = Options()
chrome_options.add_argument("--start-fullscreen")

class Window(Tk):
    def __init__(self):
        super().__init__()
        self.DRIVER = None
        self.bot_process = None
        self.stop_event = multiprocessing.Event()
        self.title("WG Gesucht Bot")
        self.geometry("1400x800")

        if self.config_exists():
            self.run_bot_ui()
        else:
            self.homepage_ui()
    
    def config_exists(self):
        return Path(".env").exists()
    
    def homepage_ui(self):
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
            self.run_button = Button(self, text="Run Bot")
            self.run_button.bind("<Button-1>", self.startBot)
            self.run_button.pack(pady=10)

            self.cancel_run_button = Button(self, text="Cancel Run")
            self.cancel_run_button.bind("<Button-1>", self.cancelRun)
            self.cancel_run_button.pack(pady=10)
    
    def cancelRun(self, event):
        if self.bot_process and self.bot_process.is_alive():
            print("Terminating bot process...")
            self.bot_process.terminate()
            self.bot_process.join()
            self.bot_process = None
            print("Bot process terminated successfully.")

    def saveConfig(self, event):
        with open(".env", "w") as f:
            f.write(f"WG_GESUCHT_USERNAME=\"{self.username.get()}\"\n")
            f.write(f"WG_GESUCHT_PASSWORD=\"{self.password.get()}\"\n")
            f.write(f"CITY=\"{self.city_text.get()}\"")
            f.write(f"WG_ZIMMER_INTRO=\"{self.wg_intro_text.get("1.0", "end-1c").replace('\n', '<nn>')}\"\n")
            f.write(f"OTHER_INTRO=\"{self.other_intro_text.get("1.0", "end-1c").replace('\n', '<nn>')}\"\n")
        self.username.delete(0, 'end')
        self.password.delete(0, 'end')
        self.city.delete(0, 'end')
        self.wg_intro_text.delete("1.0", "end-1c")
        self.other_intro_text.delete("1.0", "end-1c")

        for widget in self.winfo_children():
            widget.destroy()

        self.run_bot_ui()

    def startBot(self, event):
        if self.bot_process and self.bot_process.is_alive():
            print("Bot is already running!")
            return
        self.stop_event.clear()
        self.bot_process = multiprocessing.Process(target=self.runBot)
        self.bot_process.start()
    
    def runBot(self):
        self.DRIVER = webdriver.Chrome(options=chrome_options)
        self.DRIVER.fullscreen_window()

        room_types = [Wg_Workflow.WG_ZIMMER]

        wg = Wg_Workflow(
            driver=self.DRIVER,
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

if __name__ == "__main__":
    window = Window()
    window.mainloop()