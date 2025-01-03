import os
import shutil
import logging

logger = logging.getLogger(__name__)

def move_files_to_processed(directory, processed_directory, file_list=None):
    if not os.path.exists(processed_directory):
        os.makedirs(processed_directory)
        logger.info(f'created "processed" directory at: {processed_directory}')

    if file_list is None:
        file_list = os.listdir(directory) # list all the files in directory

    for filename in file_list:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                destination = os.path.join(processed_directory, filename)
                shutil.move(file_path, destination)
                logger.info(f"moved file '{filename}' to 'processed' directory")
            except Exception as e:
                logger.error(f"failed to move file '{filename}': {e}")
