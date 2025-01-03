### Overview
Python automation for integrating with PerfumeShop. It checks hourly for new orders and downloads them from an FTP, downloads an inventory update file, and downloads tracking numbers for orders that have already been placed.

### Main Functions:
Order Management:  
    - Downloads order files from an FTP server.  
    - Logs into a website using Selenium for order uploads.  
    - Moves successfully uploaded orders to orders/processed directory.  
    - Sends email notifications if an upload fails.  

Inventory Management:  
    - Scrapes inventory data by downloading a feed file.  
    - Uploads the scraped inventory to an FTP server.  

Fulfillment Management:  
    - Scrapes tracking data for orders that have been placed.  
    - Uploads the tracking files to an FTP server.  

Success Confirmation:  
    - If orders are successfully uploaded, a confirmation e-mail is sent with the batch number for the orders.  
    - If any of the functions fail, an e-mail alert is sent.  

### Usage
The script is controlled by a plist, set to run every hour. The plist should be added to ~/Library/LaunchAgents/ and then loaded and started. 