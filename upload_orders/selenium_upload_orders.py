import logging
import os
import re
from dotenv import load_dotenv
from utils.email_utils import send_email_attachment
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException
)
import time

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

def upload_order(driver, file_path):

    # selenium shortcuts
    driver_short_wait = WebDriverWait(driver, 10)
    driver_long_wait = WebDriverWait(driver, 30)

    def short_wait(by, value, short_wait=driver_short_wait):
            return short_wait.until(EC.element_to_be_clickable((by, value)))

    def long_wait(by, value, long_wait=driver_long_wait):
            return long_wait.until(EC.element_to_be_clickable((by, value)))

    # Check if the order is an actual file and not a dir
    if not os.path.isfile(file_path):  
        logger.error(f"File not found: {file_path}")
        return False, None
    
    batch_number = None
    oos_detected = False

    # upload the order file
    try:
        driver.get(os.getenv('UPLOAD_URL'))

        logger.info(f"Uploading file: {file_path}")
        upload_file_input = long_wait(By.ID, 'formFile')
        upload_file_input.send_keys(os.path.abspath(file_path))
        logger.info("File path sent to upload input.")

        # Click upload button for file upload
        try:
            upload_button = short_wait(By.ID, 'uploadBtn')
            logger.info("Clicking the upload submit button.")
            upload_button.click()
        except (ElementClickInterceptedException, TimeoutException) as e:
            logger.warning(f"Could not click upload submit button normally: {e}")
            upload_button = driver.find_element(By.ID, 'uploadBtn')
            driver.execute_script("arguments[0].click();", upload_button)
            logger.info("Upload file submit button clicked with fallback")

        # override address validation if necessary
        try:
             logger.info('checking for address verification prompt')
             proceed_button = short_wait(By.CLASS_NAME, 'proceedBtn')
             proceed_button.click()
        except (TimeoutException, NoSuchElementException):
             logger.info('address already verfied')

        # override OOS / partial fullfillment if necessary
        try:
            logger.info('checking for OOS message')
            oos_message = driver_short_wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'alert'))
            )
            oos_detected = True
            logger.warning(f'OOS message found: {oos_message.text}. clicking checkout button')

            # take a screenshot so we have the order number to process OOS manually
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            oos_screenshot_path = f'oos_items_{timestamp}.png'
            driver.save_screenshot(oos_screenshot_path)

            checkout_btn = short_wait(By.ID, 'submitBtn')
            driver.execute_script("arguments[0].scrollIntoView(true);", checkout_btn) #scroll into view
            driver.execute_script("arguments[0].click();", checkout_btn)
            logger.info('checout button clicked')
            time.sleep(2)

        except (TimeoutException, NoSuchElementException):
            logger.info('no items found to be out of stock')

        # submit the order
        logger.info('submitting the order')
        try:
            submit_order_btn = short_wait(By.ID, 'submitBtn')
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_order_btn) #scroll into view
            driver.execute_script("arguments[0].click();", submit_order_btn)
            logger.info('submit order button clicked')
        except (ElementClickInterceptedException, TimeoutException) as e:
             logger.warning(f"Could not click submit button normally: {e}")
             submit_order_btn = driver.find_element(By.ID, 'submitBtn')
             submit_order_btn.click()
             logger.info('clicked submit with fallback')

        # Wait for order success message & scrape it
        logger.info("Waiting for success message...")
        success_alert = driver_long_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mb-0")))
            
        success_message = success_alert.text
        logger.info(f"Success message found: {success_message}")  # Display success msg

        match = re.search(r'#(\d+)', success_message) #parse out just the batch number 
        batch_number = match.group(1) if match else None

        if oos_detected:
                send_email_attachment(
                     subject = 'PerfumeShopBot OOS', 
                     body = f'PerfumeShop orders from batch: {batch_number} had OOS items. See attachment for order number(s)',
                     attachment_path = oos_screenshot_path
                )
                    
        if batch_number:
            logger.info(f"Scraped batch number: {batch_number}")

            return True, batch_number  # If we get here, everything worked & order submitted
        
    except Exception as e:
        return False, None