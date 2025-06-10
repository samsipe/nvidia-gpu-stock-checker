from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import logging

from config import NVIDIA_URL, STATE_FILE, TARGET_GPU
from nvidia_gpu_stock_checker.state_manager import StateManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class StockChecker:
    def __init__(self):
        self.url = NVIDIA_URL
        self.state_manager = StateManager()
        logging.debug(f"Initialized StockChecker with URL: {self.url}")

    def check_stock(self):
        """Check if the GPU is in stock"""
        # Get previous state
        previous_state = self.state_manager.get_stock_state()
        previous_available = previous_state.get("available", False)

        options = webdriver.ChromeOptions()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        )
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Try default Chrome/Chromium first, fallback to system paths if needed
        try:
            driver = webdriver.Chrome(options=options)
        except WebDriverException as e:
            logging.error(f"Failed to start browser: {e}")
            self.state_manager.update_stock_state(False)
            return False, previous_available
        except Exception as e:
            logging.debug(f"Could not create Chrome driver with defaults: {e}")
            # Fallback to system-installed Chrome/Chromium
            options.binary_location = "/usr/bin/chromium"
            driver = webdriver.Chrome(
                options=options,
                service=webdriver.ChromeService(
                    executable_path="/usr/bin/chromedriver"
                ),
            )
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

                soup = BeautifulSoup(html, "html.parser")
                products = soup.find_all("div", class_="item-container")
                logging.info(f"Found {len(products)} products on the page.")
                driver.quit()

                for product in products:
                    title_elem = product.select_one(".item-title")
                    if not title_elem:
                        logging.debug(
                            "No title element found for a product card, skipping."
                        )
                        continue

                    title = title_elem.get_text().strip()
                    logging.debug(f"Checking product: {title}")
                    if TARGET_GPU in title:
                        # Check if there's an "Add to Cart" button or similar button
                        availability_elem = product.select_one(".item-operate")
                        if availability_elem:
                            availability_text = (
                                availability_elem.get_text().strip().lower()
                            )
                            is_available = (
                                "add to cart" in availability_text
                                and "out of stock" not in availability_text
                            )
                            logging.info(
                                f"{'In Stock' if is_available else 'Not Available'}: {title}"
                            )

                            # Update state and check if it changed from not available to available
                            state_changed = is_available and not previous_available
                            self.state_manager.update_stock_state(is_available)

                            # Return on the first available GPU
                            if is_available:
                                return is_available, state_changed

                # If we reached here, didn't find the product
                state_changed = (
                    False and previous_available
                )  # Only changed if was previously available
                self.state_manager.update_stock_state(False)
                return False, state_changed

            except TimeoutException:
                logging.warning(
                    f"Request timed out on attempt {attempt+1}/{max_retries}"
                )
                if attempt < max_retries - 1:
                    logging.info(f"Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                else:
                    logging.error("All retry attempts failed with timeout")
                    self.state_manager.update_stock_state(False)
                    return (
                        False,
                        previous_available,
                    )  # Only changed if was previously available
            except Exception as e:
                logging.error(f"Error checking stock: {e}")
                self.state_manager.update_stock_state(False)
                return (
                    False,
                    previous_available,
                )  # Only changed if was previously available

        # If we reached here without finding the product
        logging.warning(f"Could not find {TARGET_GPU} on the page after all attempts")
        state_changed = (
            False and previous_available
        )  # Only changed if was previously available
        self.state_manager.update_stock_state(False)
        return False, state_changed
