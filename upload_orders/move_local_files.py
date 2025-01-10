import os
import shutil
import logging

logger = logging.getLogger(__name__)

def move_files_to_processed(directory, processed_directory, file_list=None):
    if not os.path.exists(processed_directory):
        os.makedirs(processed_directory)
        logger.info(f'created "processed" directory at: {processed_directory}')

    if file_list is None:
        file_list = os.listdir(directory)

    logger.debug(f"moving files: {file_list}")
    logger.debug(f"from: {directory}")
    logger.debug(f"to: {processed_directory}")

    for filename in file_list:
        file_path = os.path.join(directory, filename)
        destination = os.path.join(processed_directory, filename)
        
        logger.debug(f"Source exists: {os.path.exists(file_path)}")
        logger.debug(f"Have write permission: {os.access(processed_directory, os.W_OK)}")
        
        if os.path.isfile(file_path):
            try:
                destination = os.path.join(processed_directory, filename)
                shutil.move(file_path, destination)
                logger.info(f"Moved file '{filename}' to '{destination}'")
            except Exception as e:
                logger.error(f"Failed to move '{filename}': {str(e)}", exc_info=True)

if __name__ == '__main__':
    move_files_to_processed()