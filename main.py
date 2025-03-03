import logging
from src.stock_checker import StockChecker
from src.sms_notifier import SMSNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting GPU stock check...")

    # Initialize stock checker
    checker = StockChecker()

    # Check if GPU is in stock
    is_available, state_changed = checker.check_stock()

    if is_available:
        logging.info("GPU is currently AVAILABLE!")

        # Only send notification if state changed from unavailable to available
        if state_changed:
            logging.info("State changed from unavailable to available. Sending notification...")
            notifier = SMSNotifier()
            notifier.send_notification()
        else:
            logging.info("GPU was already available in previous check. No notification sent.")
    else:
        logging.info("GPU is currently not available.")

if __name__ == "__main__":
    main()
