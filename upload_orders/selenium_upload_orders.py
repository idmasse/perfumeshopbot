import logging
import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException
)
import time
import re

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  


MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def upload_order(driver, file_path, short_wait_time=5, long_wait_time=30):
    if not os.path.isfile(file_path):  # Check if the order is an actual file and not a dir
        logger.error(f"File not found: {file_path}")
        return False, None

    short_wait = WebDriverWait(driver, short_wait_time)
    long_wait = WebDriverWait(driver, long_wait_time)

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Attempt {attempt + 1} of {MAX_RETRIES}: Navigating to upload page...")
            driver.get(os.getenv('UPLOAD_URL'))

            # Wait for any initial loaders to disappear
            logger.info("Waiting for initial loaders to disappear...")
            long_wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.loaderDiv')))
            logger.info("Initial loaders are now invisible.")

            logger.info(f"Uploading file: {file_path}")
            upload_file_input = long_wait.until(
                EC.presence_of_element_located((By.ID, 'formFile'))
            )
            upload_file_input.send_keys(os.path.abspath(file_path))
            logger.info("File path sent to upload input.")

            # Click upload button for file upload
            try:
                upload_button = long_wait.until(
                    EC.element_to_be_clickable((By.ID, 'uploadBtn'))
                )
                logger.info("Clicking the upload submit button.")
                upload_button.click()
            except (ElementClickInterceptedException, TimeoutException) as e:
                logger.warning(f"Could not click upload submit button normally: {e}")
                # Attempt JavaScript click as fallback
                upload_button = driver.find_element(By.ID, 'uploadBtn')
                driver.execute_script("arguments[0].click();", upload_button)
                logger.info("Upload submit button clicked using JavaScript.")

            # # Click first proceed button
            # logger.info("Clicking first 'Proceed' button.")
            # proceed_btn_1 = short_wait.until(
            #     EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[3]/div[2]/div/div[2]/button[2]")) 
            # )
            # proceed_btn_1.click()

            # # Click second proceed button
            # logger.info("Clicking second 'Proceed' button.")
            # proceed_btn_2 = short_wait.until(
            #     EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div[2]/div/div[2]/div[4]/button[2]"))
            # )
            # proceed_btn_2.click()

            # # Select 'Pay all remaining balance'
            # logger.info("Selecting option to pay entire balance.")
            # pay_remaining_balance = short_wait.until(
            #     EC.element_to_be_clickable((By.ID, 'pay0'))
            # )
            # pay_remaining_balance.click()

            # Final submit of the order
            # submit_order_btn = long_wait.until(
            #     EC.presence_of_element_located((By.ID, 'submitBtn')) 
            # )
            time.sleep(5)
            logger.info("Submitting the order.")
            submit_order_btn = driver.find_element(By.ID, 'submitBtn')
            try:
                submit_order_btn.click()
                logger.info('Clicked submit order button')
            except ElementClickInterceptedException as e:
                # JavaScript fallback for cases where the element cannot be clicked directly.
                driver.execute_script("arguments[0].click();", submit_order_btn)
                logger.info('Clicked with JS as fallback.')
                logger.warning(f"ElementClickInterceptedException caught: {e}.")

            # Scroll the submit button into view
            # driver.execute_script("arguments[0].scrollIntoView(true);", submit_order_btn)
            # logger.info("Scrolled the submit button into view.")

            # Attempt to click the submit button
            # try:
            #     driver.execute_script("arguments[0].click();", submit_order_btn)
            #     logger.info("Submit order button clicked using JavaScript.")
            # except ElementClickInterceptedException as e:
            #     logger.warning(f"ElementClickInterceptedException caught: {e}.")
                
            # Wait for any loaders to appear and disappear
            logger.info("Waiting for submission loader to appear and disappear.")
            try:
                # Wait for SweetAlert loader to appear
                long_wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '.swal2-container'))
                )
                logger.info("Submission loader appeared.")

                # Wait for SweetAlert loader to disappear
                long_wait.until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, '.swal2-container'))
                )
                logger.info("Submission loader disappeared.")
            except TimeoutException:
                logger.warning("Submission loader did not appear or did not disappear as expected.")

            # Wait for order success message & scrape it
            try:
                logger.info("Waiting for success message...")
                success_alert = long_wait.until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "div.alert.alert-success.mt-3")
                    )
                )
                success_message = success_alert.text
                logger.info(f"Success message found: {success_message}")  # Display success msg

                match = re.search(r'Batch #(\d+)', success_message)
                batch_number = match.group(1) if match else None
                if batch_number:
                    logger.info(f"Scraped batch number: {batch_number}")

                return True, batch_number  # If we get here, everything worked & order submitted

            except TimeoutException:
                logger.error("No success alert found. Order submission may have failed.")
                return False, None

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}", exc_info=True)
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying upload in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)  # Delay before retrying

    logger.error(f"All {MAX_RETRIES} attempts failed. No more retries -- quitting.")
    return False, None
