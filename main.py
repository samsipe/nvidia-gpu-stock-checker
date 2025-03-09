import logging
from nvidia_gpu_stock_checker.stock_checker import StockChecker
from nvidia_gpu_stock_checker.sms_notifier import SMSNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # First, check for subscribe/unsubscribe messages
    logging.info("Checking for subscription messages...")
    notifier = SMSNotifier()
    notifier.check_for_subscription_messages()

    # Then continue with stock checking
    logging.info("Starting GPU stock check...")
    checker = StockChecker()
    is_available, state_changed = checker.check_stock()

    if is_available:
        logging.info("GPU is currently AVAILABLE!")

        # Only send notification if state changed from unavailable to available
        if state_changed:
            logging.info("State changed from unavailable to available. Sending notification...")
            subscribers_count = len(notifier.get_subscribers())

            if subscribers_count > 0:
                notifier.send_notification()
                logging.info(f"Notification sent to {subscribers_count} subscribers.")
            else:
                logging.info("No subscribers to notify.")
        else:
            logging.info("GPU was already available in previous check. No notification sent.")
    else:
        logging.info("GPU is currently not available.")

if __name__ == "__main__":
    main()
