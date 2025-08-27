from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent
import time

ua = UserAgent(min_percentage=80, platforms='desktop')

url = "https://yandex.ru/maps/"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--user-agent={ua.random}")


with webdriver.Chrome(options=chrome_options) as browser:
    browser.get(url)

    waiter = WebDriverWait(browser, 10)
    actions = ActionChains(browser)

    # Вводим город, заведение
    search_org = browser.find_element(By.CSS_SELECTOR, "input._bold")
    search_org.send_keys("Екатеринбург, Rostics")
    find_button = browser.find_element(By.CSS_SELECTOR, 'button[aria-label="Найти"]')
    find_button.click()

    # Ищем все заведения
    last_place = None
    while True:
       time.sleep(1)
       places = browser.find_elements(By.CSS_SELECTOR, "ul.search-list-view__list > li")

       if places[-1] == last_place:
           break
    
       browser.execute_script("return arguments[0].scrollIntoView(true);", places[-1])
       last_place = places[-1]  

    # Проходимся по каждому заведению и собираем отзывы
    for place in places:
        time.sleep(1)
        browser.execute_script("return arguments[0].scrollIntoView(true);", place)
        place.click()

        review_button = browser.find_element(By.CSS_SELECTOR, "._name_reviews")
        review_button.click()

        last_review = None
        while True:
            time.sleep(1)
            reviews = browser.find_elements(By.CSS_SELECTOR, ".business-review-view__body")

            if reviews[-1] == last_review:
                break
            
            browser.execute_script("return arguments[0].scrollIntoView(true);", reviews[-1])
            last_review = reviews[-1]

        reviews_comments = []
        for review in reviews:
            browser.execute_script("return arguments[0].scrollIntoView(true);", review)

            if more_button := review.find_elements(By.CSS_SELECTOR, ".spoiler-view__button"):
                actions.move_to_element(more_button[0]).click().perform()
                actions.reset_actions()

            review_text = review.text
            reviews_comments.append(review_text)

        browser.execute_script("return arguments[0].scrollIntoView(true);", reviews[0])
        browser.back()
