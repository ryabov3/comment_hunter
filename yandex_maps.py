from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from fake_useragent import UserAgent

import time
import logging

from tqdm import tqdm

BLUE = '\033[94m'
RESET = '\033[0m'

class BlueFormatter(logging.Formatter):
    def format(self, record):
        record.msg = f"{BLUE}{record.msg}{RESET}"
        return super().format(record)

handler = logging.StreamHandler()
handler.setFormatter(BlueFormatter('%(asctime)s - %(message)s', 
                                   datefmt="%H:%M:%S"))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

for h in logger.handlers[:]:
    logger.removeHandler(h)

logger.addHandler(handler)


class YandexMaps:
    def __init__(self, city, organization):
        self._ua = UserAgent(min_percentage=80, platforms='desktop')
        self.city = city
        self.organization = organization

        self.url = "https://yandex.ru/maps/"

        self._chrome_options = webdriver.ChromeOptions()
        self._chrome_options.add_argument(f"--user-agent={self._ua.random}")
        self._chrome_options.add_argument("--headless")
        self._chrome_options.add_argument("--disable-gpu")

        self._browser = webdriver.Chrome(options=self._chrome_options)
        self._waiter = WebDriverWait(self._browser, 10)
        self._actions = ActionChains(self._browser)

        self.address_reviews = {}
    
    def _input_name_loc_org(self):
        search_org = self._waiter.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input._bold")))
        search_org.send_keys(f"{self.city}, {self.organization}")
        find_button = self._browser.find_element(By.CSS_SELECTOR, 'button[aria-label="Найти"]')
        find_button.click()
        logging.info("Input name and location of organization was successful...")
    
    def _find_all_points_orgs(self):
        last_place = None
        while True:
            time.sleep(1)
            self.places = self._browser.find_elements(By.CSS_SELECTOR, "ul.search-list-view__list > li")

            if self.places[-1] == last_place:
                break
            
            self._browser.execute_script("return arguments[0].scrollIntoView(true);", self.places[-1])
            last_place = self.places[-1]
        logging.info(f'Found all points of {self.organization}.')
    
    def _get_all_reviews(self):
        main_current_handle = self._browser.current_window_handle
        RED = '\033[91m'
        for place in tqdm(self.places, desc=f'{RED}Get reviews from places{RED}', colour='green'):
            time.sleep(0.3)
            self._browser.execute_script("return arguments[0].scrollIntoView(true);", place)
            address = place.find_element(By.CSS_SELECTOR, ".search-business-snippet-view__address").text
            
            link_review = place.find_element(By.CSS_SELECTOR, "a[class=link-overlay]").get_attribute("href")
            self._browser.switch_to.new_window("review_window")
            self._browser.get(link_review)
            self._browser.set_page_load_timeout(5)

            review_button = self._waiter.until(EC.presence_of_element_located((By.CSS_SELECTOR, "._name_reviews")))
            self._browser.execute_script("return arguments[0].scrollIntoView(true);", review_button)
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
            self._reviews = self._browser.find_elements(By.CSS_SELECTOR, ".business-review-view__body")

            if self._reviews[-1] == last_review:
                break
            
            self._browser.execute_script("return arguments[0].scrollIntoView(true);", self._reviews[-1])
            last_review = self._reviews[-1]
        logging.info('We do all reviews visibility of that place...')
    
    def __get_text_from_review(self):
        YELLOW = '\033[93m'
        self._reviews_comments = []
        for review in tqdm(self._reviews, desc=f'{YELLOW}Get reviews complete{YELLOW}', colour='green'):

            if more_button := review.find_elements(By.CSS_SELECTOR, ".spoiler-view__button"):
                self._browser.execute_script("return arguments[0].scrollIntoView(true);", review)
                self._actions.move_to_element(more_button[0]).click().perform()
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
        self._find_all_points_orgs()
        self._get_all_reviews()

        self._browser.quit()
        
        return self.address_reviews

yandex_map = YandexMaps(city='Екатеринбург', organization='Rostics')
data = yandex_map()
