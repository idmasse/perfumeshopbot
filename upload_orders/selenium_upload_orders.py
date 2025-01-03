import logging
import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re

load_dotenv()

logger = logging.getLogger(__name__)

# retry params
MAX_RETRIES = 3
RETRY_DELAY = 5 #seconds

def upload_order(driver, file_path, short_wait_time=5, long_wait_time=30):
    if not os.path.isfile(file_path): # check if the order is an actual file and not a dir
        logger.error(f"file not found: {file_path}")
        return False

    short_wait = WebDriverWait(driver, short_wait_time)
    long_wait = WebDriverWait(driver, long_wait_time)

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"attempt {attempt + 1} of {MAX_RETRIES}: navigating to upload page...")
            driver.get(os.getenv('UPLOAD_URL'))

            logger.info(f"uploading file: {file_path}")
            upload_file_input = long_wait.until(
                EC.presence_of_element_located((By.ID, 'formFile'))
            )
            upload_file_input.send_keys(os.path.abspath(file_path))

            # clck submit button for file upload
            try:
                submit_button = driver.find_element(By.ID, 'uploadBtn')
                submit_button.click()
            except Exception as e:
                logger.warning(f"could not click submit button: {e}")
                return False

            # click first proceed button
            logger.info("clicking first 'proceed' button")
            proceed_btn_1 = short_wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/div[2]/button[2]'))
            )
            proceed_btn_1.click()

            # click second proceed button
            logger.info("clicking second 'proceed' button")
            proceed_btn_2 = short_wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/form/div/div[2]/div/div[2]/div[4]/button[2]'))
            )
            proceed_btn_2.click()

            # select pay all remaining balance
            logger.info("selecting option to pay entire balance")
            pay_remaining_balance = short_wait.until(
                EC.presence_of_element_located((By.ID, 'pay0'))
            )
            pay_remaining_balance.click()

            # final submit of the order
            logger.info("submitting the order")
            submit_order_btn = long_wait.until(
                EC.presence_of_element_located((By.ID, 'submitBtn'))
            )
            submit_order_btn.click()

            try: # wait for order success message & scrape it
                logger.info("waiting for success message...")
                success_alert = long_wait.until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "div.alert.alert-success.mt-3")
                    )
                )
                success_message = success_alert.text
                logger.info(f"success message found: {success_message}")  # display success msg

                match = re.search(r'Batch #(\d+)', success_message)
                batch_number = match.group(1) if match else None
                if batch_number:
                    logger.info(f'scraped batch number: {batch_number}')

                return True, batch_number  # if we get here, everything worked & order submitted

            except TimeoutException:
                logger.error("no success alert found. order submission may have failed.")
                return False, None

        except Exception as e:
            logger.error(f"attempt {attempt + 1} failed: {e}", exc_info=True)
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.info(f"retrying upload in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)  # delay before retrying

    logger.error(f"all {MAX_RETRIES} attempts failed. no more reties --quitting")
    return False, None
