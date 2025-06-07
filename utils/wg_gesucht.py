from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langchain_core.messages import HumanMessage, SystemMessage
import os
from .config import WG_USERNAME, WG_PASSWORD
import pickle
from pathlib import Path
from time import sleep
from datetime import datetime
from .models import Apartment, ENGINE
from sqlalchemy.orm import sessionmaker
import pyperclip
import platform

class Wg_Workflow():
    EIN_ZIMMER_WOHNUNG = "1-Zimmer-Wohnung"
    WG_ZIMMER = "WG-Zimmer"
    WOHNUNG = "Wohnung"
    HAUS = "Haus"

    def __init__(self,
                 username: str,
                 password: str,
                 driver: webdriver.Chrome,
                 cookies_path: Path,
                 room_types: list[str],
                 city: str,
                 wg_intro: str,
                 other_intro: str,
                 max_budget: int = 550
                ):
        self.username = username
        self.password = password
        self.driver = driver
        self.base_url = "https://www.wg-gesucht.de/"
        self.cookies_path = cookies_path
        self.room_types = room_types
        self.city = city
        self.wg_intro = wg_intro
        self.other_intro = other_intro
        self.session = sessionmaker(bind=ENGINE)()
        self.max_budget = max_budget
    
    def make_elem_clickable_id(self, id: str):
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, id))
        )
        return element
    
    def make_elem_clickable_class(self, class_name: str):
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, class_name))
        )
        return element
    
    def login(self):
        """
            Login to wg-gesucht.de, and save cookies
        """
        self.driver.get(self.base_url)
        # check if cookies exist
        if self.cookies_path.exists():
            cookies = pickle.load(open(self.cookies_path, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)

        # Accept all cookies
        accept_cookies = self.driver.find_element(By.XPATH, '//*[@id="cmpbntyestxt"]')
        accept_cookies.click()

        # click on login
        login = self.driver.find_element(By.CLASS_NAME, 'dropdown-mini')
        login.click()

        # enter email
        username_wg = self.make_elem_clickable_id('login_email_username')
        ActionChains(self.driver).move_to_element(username_wg).click().perform()
        username_wg.send_keys(self.username)

        # enter password
        password_wg = self.make_elem_clickable_id('login_password')
        ActionChains(self.driver).move_to_element(password_wg).click().perform()
        password_wg.send_keys(self.password)

        # click on login
        login_button = self.driver.find_element(By.ID, 'login_submit')
        login_button.click()

        # save cookies
        pickle.dump(self.driver.get_cookies(), open(self.cookies_path, "wb"))

        # copy the nachricht
        pyperclip.copy(self.wg_intro)

    def search(self):
        """
            Search for rooms in a city
        """
        sleep(2)
        city_inp = self.make_elem_clickable_id("autocompinp")
        ActionChains(self.driver).move_to_element(city_inp).click().perform()
        city_inp.send_keys(self.city)

        # get autocomplete suggestions
        city_suggestions = self.make_elem_clickable_class("autocomplete-suggestion")
        ActionChains(self.driver).move_to_element(city_suggestions).click().perform()

        # select room type
        categories = self.make_elem_clickable_id("categories")
        ActionChains(self.driver).move_to_element(categories).click().perform()

        cat_types = categories.find_elements(By.TAG_NAME, "li")

        for cat_type in cat_types:
            txt = cat_type.text
            
            # turn off the default selected room type
            if cat_type.get_attribute("class") == "selected":
                ActionChains(self.driver).move_to_element(cat_type).click().perform()
            
            # check if the room type is in the list
            if txt in self.room_types:
                ActionChains(self.driver).move_to_element(cat_type).click().perform()
        
        search_btn = self.make_elem_clickable_id("search_button")
        ActionChains(self.driver).move_to_element(search_btn).click().perform()

        WebDriverWait(self.driver, 10)
        print("Initiating Search sequence")
        sleep(10)
    
    def send_message(self, msg_btn, ad_title, is_wg):
        ad_url = self.driver.current_url
        db_search = self.session.query(Apartment).filter(Apartment.url == ad_url).first()
        if db_search:
            print("\tAlready contacted the owner. Entry found in database")
            return 1

        msg_btn.click()

        try:
            print("\tSecurity check")
            security_check = self.make_elem_clickable_id("sicherheit_bestaetigung")
            security_check.click()
            sleep(1)
        except Exception as e:
            print("\tNo security check")
        
        ad_author = "Unknown"
        try:
            ad_author = self.driver.find_element(By.XPATH, '//*[@id="start_new_conversation"]/div[1]/div/div[2]/div/div[2]/b')
            ad_author = ad_author.text.strip()
        except Exception as e:
            print("\tNo author found")
        nachricht = None

        if is_wg:
            nachricht = self.wg_intro
            pyperclip.copy(self.wg_intro)
        else:
            nachricht = self.other_intro
            pyperclip.copy(self.other_intro)
            
        txt_area = self.driver.find_element(By.ID, 'message_input')
        if platform.system() == 'Darwin':
        # txt_area.send_keys(nachricht)
            txt_area.send_keys(Keys.COMMAND, "v")
        else:
            txt_area.send_keys(Keys.CONTROL, "v")
        try:
            senden_btn = self.driver.find_element(By.XPATH, '//*[@id="messenger_form"]/div[1]/div[4]/div[2]/div[2]/button')
            senden_btn.click()
        except Exception as e:
            print("\tAlready contacted but not in the database")
        
        new_apt = Apartment(
            url=ad_url,
            author=ad_author,
            ad_title=ad_title,
            is_wg=is_wg
        )
        self.session.add(new_apt)
        self.session.commit()
        print("\tMessage sent")
        
        sleep(5)
        return 0

    def find_and_click_first_not_contacted(self):
        page_num = 1
        while True:
            print(f"\t\t Searching for ads not contacted on page {page_num}")
            all_ads = self.driver.find_elements(By.CLASS_NAME, "offer_list_item")
            for ad in all_ads:
                try:
                    ad.find_element(By.CLASS_NAME, "ribbon-contacted")
                except Exception as e:
                    ad_title =  ad.find_element(By.TAG_NAME, "h3").text
                    if self.session.query(Apartment).filter(Apartment.ad_title == ad_title).first():
                        continue
                    ad.find_element(By.TAG_NAME, "h3").click()
                    return
            
            next_elems = self.driver.find_elements(By.CLASS_NAME, "next")
            for elem in next_elems:
                if elem.get_attribute("class").find("page-link") != -1:
                    elem.click()
                    break
            page_num += 1
    
    def get_through_rooms(self):
        """
            Check if the panel is an Advertisement. If it's not click the first item
        """
        i = 1
        contacted_count = 0

        # panels = self.driver.find_elements(By.CLASS_NAME, "offer_list_item")

        # for panel in panels:
        #     panel.find_element(By.TAG_NAME, "h3").click()
        #     print("Clicked on the first advertisment")
        #     break

        max_budget = self.make_elem_clickable_id("rMax")
        max_budget.send_keys(self.max_budget)
        filter_btn = self.driver.find_element(By.XPATH, '//*[@id="offer_filter_form"]/div[3]/div[3]/button[2]')
        filter_btn.click()

        self.find_and_click_first_not_contacted()
        
        sleep(10)

        while i < 100:
            # get the url of the page and click on the next button
            print(f"Page number: {i}", self.driver.current_url, sep=" - ")

            ad_title_container = self.driver.find_element(By.XPATH, '//*[@id="main_column"]/div[4]/div/div/div[1]/div/h1')
            ad_title = None
            is_wg = False

            if len(ad_title_container.find_elements(By.XPATH, "./*")) == 1:
                ad_title = self.driver.find_element(By.XPATH, '//*[@id="main_column"]/div[4]/div/div/div[1]/div/h1/span')
            else:
                is_wg = True
                ad_title = self.driver.find_element(By.XPATH, '//*[@id="main_column"]/div[4]/div/div/div[1]/div/h1/span[2]')

            ad_title = ad_title.text.strip()
            
            print(f"\tAd title: {ad_title} - Ad type: {'WG' if is_wg else 'Other'}")
            # get the Nachricht senden button
            nachricht_senden = self.driver.find_element(By.XPATH, '//*[@id="utilities_rhs"]/div[3]/div/a')
            
            # check the availability of the apartment
            frei_ab = None
            frei_bis = None
            try:
                frei_ab = self.driver.find_element(By.XPATH, '//*[@id="main_column"]/div[6]/div/div/div/div[2]/div[1]/div[2]/span')
                frei_ab = frei_ab.text.strip()
                frei_ab = datetime.strptime(frei_ab, "%d.%m.%Y")
                print("\t", frei_ab.strftime("%d.%m.%Y"), end=" - ")
            except Exception as e:
                print(e)
            
            try:
                frei_bis = self.driver.find_element(By.XPATH, '//*[@id="main_column"]/div[6]/div/div/div/div[2]/div[2]/div[2]/span')
                frei_bis = frei_bis.text.strip()
                frei_bis = datetime.strptime(frei_bis, "%d.%m.%Y")
                print("\t", frei_bis.strftime("%d.%m.%Y"))
            except Exception as e:
                print(f"\tAsk the owner")
            
            # frei bis does not exist then it's not a sublet
            if not frei_bis:
                frei_bis = datetime.strptime("01.01.2026", "%d.%m.%Y")
            
            if (frei_bis - frei_ab).days > 180:
                # send message
                contacted = self.send_message(nachricht_senden, ad_title, is_wg)
                contacted_count += contacted

                if not contacted:
                    self.driver.back()

                if contacted_count > 10:
                    # Click on Treffer button
                    self.driver.find_element(By.XPATH, '//*[@id="main_column"]/div[1]/div[2]/div/a').click()
                    sleep(1)
                    self.find_and_click_first_not_contacted()
            else:
                if not self.session.query(Apartment).filter(Apartment.ad_title == ad_title).first():
                    new_apt = Apartment(
                        url=self.driver.current_url,
                        author="Unknown",
                        ad_title=ad_title,
                        is_wg=is_wg
                    )
                    self.session.add(new_apt)
                    self.session.commit()
                print(f"\tSkipping: Sublet duration is {(frei_bis - frei_ab).days/30} months")
            
            next_elems = self.driver.find_elements(By.CLASS_NAME, "next")

            for next_elem in next_elems:
                if next_elem.get_attribute("href") is not None:
                    next_elem.click()
                    break

            i += 1
            sleep(10)
        