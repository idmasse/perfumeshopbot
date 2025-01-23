import os
from dotenv import load_dotenv
from upload_orders.selenium_upload_orders import upload_order
from upload_orders.move_local_files import move_files_to_processed
from inventory_scraper.scrape_inventory import scrape_inventory
from tracking_scraper.scrape_tracking import scrape_tracking
from utils.selenium_login import perfume_selenium_login, logger
from utils.ftp_utils import connect_ftp, download_files, delete_files_on_ftp, archive_files_on_ftp
from utils.selenium_setup import get_headless_driver
from utils.email_utils import send_email

load_dotenv()

# website login credentials
LOGIN_USERNAME = os.getenv('LOGIN_USERNAME')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')

# local directories
LOCAL_ORDERS_DIR = os.getenv('LOCAL_ORDERS_DIR')
LOCAL_PROCESSED_DIR = os.getenv('LOCAL_PROCESSED_DIR')

upload_orders_success = False

def upload_orders():
    global upload_orders_success
    batch_numbers = []
    
    # 1. connect to FTP & download files
    ftp = connect_ftp()
    downloaded_files = []
    if ftp:
        try:
            downloaded_files = download_files(ftp)  # download files from FTP
            if downloaded_files:
                archive_files_on_ftp(ftp, downloaded_files)  # archive downloaded files from FTP
        finally:
            ftp.quit()
            logger.info("FTP connection closed")

    # if no files are downloaded --quit
    if not downloaded_files:
        logger.info("no files downloaded. nothing to do. byeee!")
        return #quit main() if no files found

    # 2. login to PerfumeShop
    driver = get_headless_driver()
    try:
        logged_in = perfume_selenium_login(driver, LOGIN_USERNAME, LOGIN_PASSWORD)
        if not logged_in:
            logger.error("login failed --qutting main script.")
            driver.quit()
            return None #quit main() if login fails

        # 3. process each order file individually
        for file_name in downloaded_files:
            file_path = os.path.join(LOCAL_ORDERS_DIR, file_name) # get file path of order to upload
            logger.info(f"starting upload for file: {file_name}")

            success, batch_number = upload_order(driver, file_path) # call the upload_order function from upload_orders.py
            if success:
                if batch_number:
                    batch_numbers.append(batch_number)
                    logger.info(f"successfully uploaded {file_name} from batch number: {batch_number}. Moving order file to the 'processed' directory.")
                # 4 move this single order file to 'processed' dir
                move_files_to_processed(LOCAL_ORDERS_DIR, LOCAL_PROCESSED_DIR, [file_name])
                upload_orders_success = True
            else:
                error_message = f"failed to upload {file_name}"
                logger.warning(f'failed to upload {file_name}, leaving it in orders directory.')
                send_email('perfumebot failed to upload order', error_message)
            
            driver.get(os.getenv('UPLOAD_URL')) #5 reset to upload page for next order
        
        return batch_numbers if batch_numbers else None

    except Exception as e:
        logger.error(f"selenium login failed: {e}", exc_info=True)
    finally:
        logger.info("quitting browser")
        driver.quit()
        logger.info("browser closed")

def scrape_inventory_to_ftp():
    try:
        scraped_and_uploaded_inventory = scrape_inventory()
        if scraped_and_uploaded_inventory:
            logger.info('inventory file successfully downloaded from vendor and uploaded to FTP')
    except Exception as e:
        logger.error(f"failed to upload inventory to FTP: {e}", exc=True)

def scrape_tracking_to_ftp():
    try:
        scraped_and_uploaded_tracking = scrape_tracking()
        if scraped_and_uploaded_tracking:
            logger.info('tracking file successfully downloaded from site and uploaded to FTP')
    except Exception as e:
        logger.error(f"failed to upload tracking to FTP: {e}", exc_info=True)


if __name__ == '__main__':
    batch_numbers = upload_orders()
    scrape_inventory_to_ftp()
    scrape_tracking_to_ftp()

    # check if all functions completed successfully and if so, send an email
    if upload_orders_success:
        batch_numbers_str = ', '.join(batch_numbers) if batch_numbers else 'no batch numbers'
        success_message = f"PerfumeShopBot completed successfully. Processed batches: {batch_numbers_str}"
        send_email("PerfumeBot ran successfully", success_message)
        logger.info("order submission success email sent.")  