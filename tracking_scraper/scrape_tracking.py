import os
import sys
import logging
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.ftp_utils import connect_ftp, upload_files
from utils.email_utils import send_email
from utils.selenium_login import perfume_selenium_login
from utils.selenium_setup import get_headless_driver
from datetime import datetime, timedelta
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

LOGIN_USERNAME = os.getenv('LOGIN_USERNAME')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')

def download_tracking_to_csv():
    logger.info('starting job to scrape tracking file')
    driver = get_headless_driver()
    logged_in = perfume_selenium_login(driver, LOGIN_USERNAME, LOGIN_PASSWORD)
    if not logged_in:
        logger.info('Log in failed --quitting')
        driver.quit()
        return None
    
    try:
        #format the url to download the tracking file
        today = datetime.today()
        one_week_prior = today - timedelta(days=7) # 7 days prior
        date_range = f"{one_week_prior.strftime('%Y-%m-%d')}_{today.strftime('%Y-%m-%d')}"
        orders_page_url = os.getenv('ORDERS_PAGE_URL')
        url = f"{orders_page_url}?status=2&date={date_range}&view=150"

        driver.get(url)

        wait = WebDriverWait(driver, 20)

        download_csv_button = wait.until(
            EC.element_to_be_clickable((By.ID, 'csvBtn'))
        )

        download_csv_button.click()
        logger.info("clicked the download csv button.")

        time.sleep(3)  # wait for the popup to appear

        confirm_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button.swal2-confirm.swal2-styled.swal2-default-outline')
            )
        )

        confirm_button.click()
        logger.info("clicked the confirm download button in the popup.")

        filename = '4101_tps_tracking.csv'
        return filename

    except Exception as e:
        logger.exception("failed to download tracking file.")
        return None
    finally:
        time.sleep(5)  # wait for file to download before closing
        driver.quit()

def upload_tracking_to_ftp(filename, remote_directory='/in/fulfillments'):
    downloads_path = os.path.expanduser('~/Downloads')
    local_path = os.path.join(downloads_path, filename)

    if not os.path.isfile(local_path):
        logger.error(f"file does not exist: {local_path}")
        send_email('FTP upload failed (Tracking)', f'file does not exist: {local_path}')
        return False

    remote_path = os.path.join(remote_directory, os.path.basename(local_path))

    ftp = connect_ftp()
    if not ftp:
        logger.error("Failed to connect to FTP server.")
        send_email('FTP connection failed (Tracking)', "failed to connect to FTP server.")
        return False

    try:
        # upload the file
        upload_files(ftp,  local_path, remote_path)
        logger.info(f"successfully uploaded '{local_path}' to FTP: '{remote_path}'")
        return True
    except Exception as e:
        logger.exception(f"error uploading '{local_path}' to FTP.")
        send_email('FTP upload failed (tracking)', f"error uploading '{local_path}': {e}")
        return False
    finally:
        ftp.quit()
        logger.info("FTP connection closed")

def delete_tracking_file_after_upload(filename, downloads_dir='~/Downloads'):
    try:
        downloads_path = os.path.expanduser(downloads_dir)
        file_path = os.path.join(downloads_path, filename)
        
        if os.path.isfile(file_path):
            os.remove(file_path)
            logger.info(f"successfully deleted the file: {file_path}")
            return True
        else:
            logger.warning(f"file not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.exception(f"failed to delete the tracking file {filename}: {e}")
        send_email('tracking file deletion failed', f"failed to delete the tracking file {filename}: {e}")
        return False

def scrape_tracking():
    downloaded_filename = download_tracking_to_csv()
    if not downloaded_filename:
        logger.error("download tracking failed --quitting")
        return False

    uploaded = upload_tracking_to_ftp(downloaded_filename)
    if not uploaded:
        logger.error("upload step failed --quitting")
        return False

    deleted = delete_tracking_file_after_upload(downloaded_filename)
    if not deleted:
        logger.warning(f"file {downloaded_filename} was not deleted from downloads folder.")

    logger.info("tracking file successfully downloaded, uploaded to FTP, and deleted locally.")
    return True

if __name__ == '__main__':
    scrape_tracking()
    delete_tracking_file_after_upload()
