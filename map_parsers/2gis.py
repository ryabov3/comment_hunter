from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from fake_useragent import UserAgent

import time
import logging

from tqdm import tqdm

BLUE = "\033[94m"
RESET = "\033[0m"


class BlueFormatter(logging.Formatter):
    def format(self, record):
        record.msg = f"{BLUE}{record.msg}{RESET}"
        return super().format(record)


handler = logging.StreamHandler()
handler.setFormatter(BlueFormatter("%(asctime)s - %(message)s", datefmt="%H:%M:%S"))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

for h in logger.handlers[:]:
    logger.removeHandler(h)

logger.addHandler(handler)


class TwoGis:
    def __init__(self, city, organization, path_to=None):
        self._ua = UserAgent(min_percentage=80, platforms="desktop")
        self.city = city
        self.organization = organization
        self.path_to = path_to

        self.url = "https://2gis.ru/"

        self._chrome_options = webdriver.ChromeOptions()
        self._chrome_options.add_argument(f"--user-agent={self._ua.random}")
        self._chrome_options.add_argument("--headless")
        self._chrome_options.add_argument("--disable-gpu")

        self._browser = webdriver.Chrome(options=self._chrome_options)
        self._waiter = WebDriverWait(self._browser, 10)
        self._actions = ActionChains(self._browser)

        self.address_reviews = {}
    
    def _input_name_loc_org(self):
        search_org = self._waiter.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "._cu5ae4"))
        )
        search_org.send_keys(f"{self.city}, {self.organization}")
        self._actions.move_to_element(search_org).send_keys(Keys.ENTER).perform()
        logging.info("Input name and location of organization.")
    
    def _find_all_points_org(self):
        self._all_urls_places = []
        while True:
            places = self._waiter.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "._zjunba a"))
            )
            urls_places = [place.get_attribute('href') for place in places]
            self._all_urls_places.extend(urls_places)

            try:
                if cookie_off_button := self._browser.find_elements(By.CSS_SELECTOR, "._13xlah4 > svg"):
                    cookie_off_button[0].click()
                    
                next_page_button = self._browser.find_element(
                    By.CSS_SELECTOR, "._5ocwns > ._n5hmn94:nth-child(2) > svg"
                )
                self._browser.execute_script(
                    "return arguments[0].scrollIntoView(true);", next_page_button
                )
                self._actions.move_to_element(next_page_button).click().perform()
            except NoSuchElementException:
                logging.info("Got links on all places.")
                break
    
    def _get_all_reviews(self):
        main_current_handle = self._browser.current_window_handle
        for url_place in self._all_urls_places:
            self._browser.switch_to.new_window("place")
            self._browser.get(url_place)
            self._browser.set_page_load_timeout(5)

            address = self._waiter.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "._13eh3hvq ._14quei ._wrdavn:nth-child(1) > a")
                ))
            self._browser.execute_script("return arguments[0].scrollIntoView(true);", address)

            review_button = self._waiter.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div._9idr87 div._jro6t0 ._1kmhi0c:nth-child(3) a")
            ))
            self._browser.execute_script(
                "return arguments[0].scrollIntoView(true);", review_button
            )
            review_button.click()

            self.__do_review_visibility()
            self.__get_text_from_review()
            self.__save_reviews_to_address(address)
        
            self._browser.close()
            self._browser.switch_to.window(main_current_handle)

    def __do_review_visibility(self):
        last_review = None
        while True:
            time.sleep(1)
            self._reviews = self._browser.find_elements(By.CSS_SELECTOR, "._1k5soqfl")

            if self._reviews[-1] == last_review:
                break

            self._browser.execute_script(
                "return arguments[0].scrollIntoView(true);", self._reviews[-1]
            )
            last_review = self._reviews[-1]
        logging.info("We do all reviews visibility of that place...")

    def __get_text_from_review(self):
        YELLOW = "\033[93m"
        self._reviews_comments = []
        for review in tqdm(
            self._reviews, desc=f"{YELLOW}Get reviews complete{YELLOW}", colour="green"
        ):

            if more_button := review.find_elements(By.CSS_SELECTOR, "span._17ww69i"):
                self._browser.execute_script(
                    "return arguments[0].scrollIntoView(true);", review
                )
                more_button[0].click()
                self._actions.reset_actions()

            review_text = review.text
            self._reviews_comments.append(review_text)

    def __save_reviews_to_address(self, address):
        self.address_reviews[address] = self._reviews_comments
        logging.info(f"Successful save reviews to {address}.")

    def __call__(self, *args, **kwds):
        self._browser.get(self.url)
        self._browser.set_page_load_timeout(5)

        self._input_name_loc_org()
        self._find_all_points_org()
        self._get_all_reviews()

        self._browser.quit()
        return self.address_reviews


twogis = TwoGis(city="Екатеринбург", organization="Жизньмарт")
twogis()