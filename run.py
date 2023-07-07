import os
import json
import time
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def check_proxy(test_proxy):
    try:
        response = requests.get('https://www.google.com', proxies={'http': test_proxy,'https': test_proxy}, timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False

def find_first_env_file(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.env'):
                return os.path.join(root, file)
    return None

def scrape_quotes(url):
    options = Options()
    options.add_argument("--headless")
    if proxy is not None:
        if good_proxy:
            options.add_argument(f"--{proxy}")
    driver = webdriver.Chrome(options=options) 
    driver.get(url)
    wait = WebDriverWait(driver, 40)
    try:
        next_url = ""
        wait.until(EC.presence_of_element_located((By.ID, "quotesPlaceholder")))        
        next_li = driver.find_elements(By.CSS_SELECTOR, "li.next")
        if next_li:
            for li_element in next_li:
                a_tags = li_element.find_elements(By.TAG_NAME, "a")
                for a_tag in a_tags:
                    next_url = a_tag.get_attribute("href")
                    print(f"Current scraped url:{url}\nNext url:{next_url}")
                    break
        else:
            print(f"Current scraped url: {url}\nNext url: Reached the last page to scrape.")
        quote_divs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#quotesPlaceholder .quote")))
        scraped_data = []
        for quote in quote_divs:
            soup = BeautifulSoup(quote.get_attribute("innerHTML"), "html.parser")
            text = soup.find("span", class_="text").text
            ##Strange formatting characters in the output file have been omitted
            text = text.replace("\u201c", "").replace("\u201d", "")
            author = soup.find("small", class_="author").text
            tags = [tag.text for tag in soup.find_all("a", class_="tag")]
            scraped_data.append({"text": text, "by": author, "tags": tags})
        if next_li:
            return scraped_data, False,next_url
        else:
            return scraped_data, True,None
    finally:
        driver.quit()

def save_quotes_to_json(data):
    try:
        with open(output_file, "r") as file:
            quotes = json.load(file)
    except FileNotFoundError:
        quotes = []
    
    quotes.extend(data)
    
    with open(output_file, "w") as file:
        json.dump(quotes, file, indent=4)

def main():
    first_Page = True
    next_url = ""
    while True:
        if first_Page :
            url = f"{input_url}"
            first_Page = False
        else:
            url = f"{next_url}"
        quotes, is_last_page, next_page = scrape_quotes(url)
        next_url = next_page
        save_quotes_to_json(quotes)
        if is_last_page:
            print("Scraped last page. Stopping...")
            break
        time.sleep(scrape_next_page_delay_seconds)

    print("Scraping completed!")

if __name__ == "__main__":
    #I have issues with load_dotenv() even though I provided env file in run.py directory, so it's a workaround.
    scrape_next_page_delay_seconds = 2
    good_proxy = False
    load_dotenv()
    proxy = os.environ.get('PROXY')
    input_url = os.environ.get('INPUT_URL')
    output_file = os.environ.get('OUTPUT_FILE')
    if input_url is None and output_file is None:
        env_file_path = find_first_env_file(os.getcwd())
        if env_file_path:
            load_dotenv(env_file_path)
            proxy = os.environ.get('PROXY')
            input_url = os.environ.get('INPUT_URL')
            output_file = os.environ.get('OUTPUT_FILE')
    
    if check_proxy(proxy):
        good_proxy = True
        print("Provided proxy will be used.")
    else:
        print("Provided proxy won't be used.")
    main()