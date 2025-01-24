import os
import time
import logging
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

MAX_RETRIES = 3
RETRY_DELAY = 5 # seconds

def perfume_selenium_login(driver, username, password, short_wait_time=5, long_wait_time=30):
    short_wait = WebDriverWait(driver, short_wait_time)
    long_wait = WebDriverWait(driver, long_wait_time)

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"attempt {attempt + 1} of {MAX_RETRIES}: navigating to PerfumeShop login page...")
            driver.get(os.getenv('LOGIN_URL'))

            # click the 'ok' button if it appears (preious session timeout)
            try:
                logger.info("checking for 'ok' button...")
                okay_button = short_wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'swal2-confirm'))
                )
                logger.info("'ok' button found. clicking it now...")
                okay_button.click()
            except Exception:
                logger.info("'ok' button not found or not needed. continuing...")

            # login flow
            logger.info("waiting for username field...")
            username_field = long_wait.until(
                EC.presence_of_element_located((By.NAME, 'user'))
            )

            logger.info("found username field. waiting for password field...")
            password_field = long_wait.until(
                EC.presence_of_element_located((By.NAME, 'pw'))
            )

            logger.info("entering username and password...")
            username_field.send_keys(username)
            password_field.send_keys(password)

            logger.info("clicking login button...")
            login_button = driver.find_element(By.ID, 'submitBtn')
            login_button.click()

            logger.info("login submitted. Waiting for login confirmation message...")
            long_wait.until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Welcome, Gabrielle")
            )
            logger.info("successfully logged in.")
            return True

        except Exception as e:
            logger.error(f"attempt {attempt + 1} failed: {e}", exc_info=True)
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.info(f"retrying login in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

    logger.error(f"all {MAX_RETRIES} attempts failed. no more retires.")
    return False