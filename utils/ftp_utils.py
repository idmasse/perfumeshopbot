import os
import logging
import sys
from dotenv import load_dotenv
from ftplib import FTP, error_perm, error_temp, error_reply

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FTP creds
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

LOCAL_ORDERS_DIR = os.getenv('LOCAL_ORDERS_DIR')
LOCAL_PROCESSED_DIR = os.getenv('LOCAL_PROCESSED_DIR')

REMOTE_ORDERS_DIR = '/out/orders'
REMOTE_INVENTORY_DIR='/in/inventory'

def connect_ftp():
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        logger.info(f"successfully connected to FTP server: {FTP_HOST}")
        return ftp
    except error_perm as e:
        logger.error(f"permission error: {e}")
    except error_temp as e:
        logger.error(f"temporary error: {e}")
    except error_reply as e:
        logger.error(f"reply error: {e}")
    except Exception as e:
        logger.error(f"failed to connect to FTP server: {e}")
    return None

def download_files(ftp):
    downloaded_files = []  # list to keep track of files that are downloaded
    try:
        ftp.cwd(REMOTE_ORDERS_DIR)
        files = ftp.nlst()  # list all files
        logger.info(f"list of files in remote directory: {files}")
        
        csv_files = [file for file in files if file.endswith('.csv')] #locate the csv files
        
        if not csv_files:
            # sys.exit(0)  # exit if no csv files are found
            return

        for file_name in csv_files:
            local_file_path = os.path.join(LOCAL_ORDERS_DIR, file_name)
            with open(local_file_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {file_name}', local_file.write)
            downloaded_files.append(file_name)
            logger.info(f"downloaded: {file_name}")

        return downloaded_files
    except Exception as e:
        logger.error(f"error during file download: {e}")
    return []

def delete_files_on_ftp(ftp, files):
    try:
        ftp.cwd(REMOTE_ORDERS_DIR)
        for file_name in files:
            ftp.delete(file_name)
            logger.info(f"deleted file from remote directory: {file_name}")
    except Exception as e:
        logger.error(f"error deleting files on FTP: {e}")
        sys.exit(1)

def upload_files(ftp, local_file_path, remote_file_name):
    try:
        ftp.cwd(REMOTE_INVENTORY_DIR)
        with open(local_file_path, 'rb') as local_file:
            ftp.storbinary(f'STOR {remote_file_name}', local_file)
    except Exception as e:
        logger.error(f"error during file upload: {e}")
        sys.exit(1)