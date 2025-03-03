import json
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import logging


from config import NVIDIA_URL, STATE_FILE, TARGET_GPU

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StockChecker:
    def __init__(self):
        self.url = NVIDIA_URL
        self.state_file = STATE_FILE
        self.previous_state = self.load_previous_state()
        logging.debug(f"Initialized StockChecker with URL: {self.url} and state file: {self.state_file}")

    def load_previous_state(self):
        """Load previous availability state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logging.debug(f"Loaded previous state: {state}")
                    return state
            except Exception as e:
                logging.error(f"Error loading previous state: {e}")
                return {"available": False, "last_checked": None}
        logging.debug("No previous state file found, returning default state.")
        return {"available": False, "last_checked": None}

    def save_current_state(self, state):
        """Save current availability state to file"""
        state["last_checked"] = time.time()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
                logging.debug(f"Saved current state: {state}")
        except Exception as e:
            logging.error(f"Error saving state: {e}")

    def check_stock(self):
        """Check if the GPU is in stock"""
        options = webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        # Number of retry attempts
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                logging.info(f"Attempt {attempt+1}/{max_retries} to check stock")
                # Increase timeout to give more time for the response
                driver.get(self.url)
                html = driver.page_source

                soup = BeautifulSoup(html, 'html.parser')
                products = soup.find_all('div', class_='item-container')
                logging.info(f"Found {len(products)} products on the page.")
                driver.quit()

                for product in products:
                    title_elem = product.select_one('.item-title')
                    if not title_elem:
                        logging.debug("No title element found for a product card, skipping.")
                        continue

                    title = title_elem.get_text().strip()
                    logging.debug(f"Checking product: {title}")
                    if TARGET_GPU in title:
                        # Check if there's an "Add to Cart" button or similar button
                        availability_elem = product.select_one('.item-operate')
                        if availability_elem:
                            availability_text = availability_elem.get_text().strip().lower()
                            is_available = 'add to cart' in availability_text and 'out of stock' not in availability_text
                            logging.info(f"{'In Stock' if is_available else 'Not Available'}: {title}")

                            current_state = {"available": is_available, "last_checked": time.time()}

                            # Check if state changed from unavailable to available
                            state_changed = is_available and not self.previous_state.get("available", False)

                            # Save current state
                            self.save_current_state(current_state)

                            # Return on the first available GPU
                            if is_available:
                                return is_available, state_changed

                # If we reached here, didn't find the product
                self.save_current_state({"available": False, "last_checked": time.time()})
                return False, False


            except TimeoutException:
                logging.warning(f"Request timed out on attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    logging.info(f"Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                else:
                    logging.error("All retry attempts failed with timeout")
                    self.save_current_state({"available": False, "last_checked": time.time()})
                    return False, False
            except Exception as e:
                logging.error(f"Error checking stock: {e}")
                self.save_current_state({"available": False, "last_checked": time.time()})
                return False, False

        # If we reached here without finding the product
        logging.warning(f"Could not find {TARGET_GPU} on the page after all attempts")
        self.save_current_state({"available": False, "last_checked": time.time()})
        return False, False
