import os
import sys
import logging
import requests
from dotenv import load_dotenv
from utils.ftp_utils import connect_ftp, upload_files
from utils.email_utils import send_email

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def download_inventory_to_csv(output_filename='shopify.csv'):
    session = requests.Session()

    login_url = os.getenv('INVENTORY_LOGIN_URL')
    login_data = {
        'login_email': os.getenv('LOGIN_USERNAME'),
        'login_pass': os.getenv('LOGIN_PASSWORD'),
    }

    # attempt login
    logger.info('starting job to scrape inventory')
    logger.info("logging into vendor site")
    login_response = session.post(login_url, data=login_data)
    if not login_response.ok:
        logger.error("failed to login to download inventory")
        send_email('inventory login failed', "failed to login to download inventory")
        return False

    # download inventory file
    logger.info("login successful. downloading inventory file...")
    inventory_url = os.getenv('INVENTORY_FILE_URL')
    inventory_url_response = session.get(inventory_url)
    if not inventory_url_response.ok:
        logger.error("failed to download inventory file")
        send_email('inventory file download failed', "failed to download inventory file")
        return False

    # save csv locally
    try:
        with open(output_filename, 'wb') as f:
            f.write(inventory_url_response.content)
        logger.info(f"inventory file saved as '{output_filename}'")
        return True
    except Exception as e:
        logger.error(f"error writing file '{output_filename}': {e}")
        send_email('inventory file write failed', str(e))
        return False

def upload_inventory_to_ftp(local_path, remote_directory='/in/inventory'):
    remote_path = os.path.join(remote_directory, os.path.basename(local_path))

    ftp = connect_ftp()
    if not ftp:
        logger.error("failed to connect to FTP server")
        send_email('FTP connection failed (inventory)', "failed to connect to FTP server")
        return False

    try:
        upload_files(ftp, local_path, remote_path)
        logger.info(f"successfully uploaded '{local_path}' to FTP as '{remote_path}'")
        return True
    except Exception as e:
        logger.error(f"error uploading '{local_path}' to FTP: {e}")
        send_email('FTP upload failed', str(e))
        return False
    finally:
        ftp.quit()
        logger.info('FTP connection closed')

def scrape_inventory():
    output_filename = 'shopify.csv'
    
    # download inventory file
    downloaded = download_inventory_to_csv(output_filename)
    if not downloaded:
        logger.error("download step failed. aborting scrape_inventory.")
        return False

    # upload inventory file
    uploaded = upload_inventory_to_ftp(output_filename)
    if not uploaded:
        logger.error("upload step failed. aborting scrape_inventory.")
        return False

    return True

if __name__ == '__main__':
    scrape_inventory()