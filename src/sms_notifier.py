import logging
from datetime import datetime, timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient

from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
    TARGET_GPU, NVIDIA_URL, SUBSCRIBE_KEYWORD, UNSUBSCRIBE_KEYWORD
)
from src.state_manager import StateManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set Twilio HTTP client logger to WARNING level
logging.getLogger('twilio.http_client').setLevel(logging.WARNING)

class SMSNotifier:
    def __init__(self):
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.from_number = TWILIO_FROM_NUMBER
        self.state_manager = StateManager()

        # Initialize Twilio client
        if all([self.account_sid, self.auth_token, self.from_number]):
            # Create a custom HTTP client with reduced logging
            http_client = TwilioHttpClient()
            self.client = Client(self.account_sid, self.auth_token, http_client=http_client)
        else:
            logging.error("SMS configuration is incomplete. Check your environment variables.")
            self.client = None

    def send_notification(self):
        """Send SMS notification to all subscribers that GPU is in stock"""
        if not self.client:
            logging.error("SMS client not initialized. Cannot send notifications.")
            return False

        subscribers = self.state_manager.get_subscribers()
        if not subscribers:
            logging.warning("No subscribers to notify.")
            return False

        try:
            successful_sends = 0

            for to_number in subscribers:
                try:
                    # Create and send message
                    message = self.client.messages.create(
                        body=f"🚨 ALERT: {TARGET_GPU} IS NOW IN STOCK! Check stock immediately: {NVIDIA_URL}",
                        from_=self.from_number,
                        to=to_number
                    )
                    logging.info(f"SMS notification sent to {to_number} with SID: {message.sid}")
                    successful_sends += 1
                except Exception as e:
                    logging.error(f"Error sending SMS to {to_number}: {e}")

            logging.info(f"Notification sent to {successful_sends}/{len(subscribers)} subscribers")
            return successful_sends > 0

        except Exception as e:
            logging.error(f"Error sending notifications: {e}")
            return False

    def add_subscriber(self, phone_number):
        """Add a new subscriber to the notification list"""
        return self.state_manager.add_subscriber(phone_number)

    def remove_subscriber(self, phone_number):
        """Remove a subscriber from the notification list"""
        return self.state_manager.remove_subscriber(phone_number)

    def get_subscribers(self):
        """Return the list of subscribers"""
        return self.state_manager.get_subscribers()

    def check_for_subscription_messages(self):
        """Check for new incoming messages and process subscription requests"""
        if not self.client:
            logging.error("SMS client not initialized. Cannot check messages.")
            return

        try:
            # Get the date of the last message we processed
            last_message_date = self.state_manager.get_last_message_date()

            # Format for storing in the state file (ISO format)
            now_iso = datetime.now(timezone.utc).isoformat()

            # List messages sent to our Twilio number
            messages = self.client.messages.list(to=self.from_number)

            if not messages:
                logging.info("No messages found.")
                self.state_manager.update_last_message_date(now_iso)
                return

            # Process new messages
            processed_count = 0
            for message in messages:
                # Skip messages we've already processed
                if last_message_date and message.date_created.isoformat() <= last_message_date:
                    break

                processed_count += 1
                body = message.body.strip().upper()
                from_number = message.from_

                if SUBSCRIBE_KEYWORD in body:
                    if self.add_subscriber(from_number):
                        self._send_reply(from_number, f"You've been subscribed to {TARGET_GPU} stock alerts! Reply '{UNSUBSCRIBE_KEYWORD}' to unsubscribe.")
                    else:
                        self._send_reply(from_number, f"You're already subscribed to {TARGET_GPU} stock alerts.")

                elif UNSUBSCRIBE_KEYWORD in body:
                    if self.remove_subscriber(from_number):
                        self._send_reply(from_number, f"You've been unsubscribed from {TARGET_GPU} stock alerts. Reply '{SUBSCRIBE_KEYWORD}' to subscribe again.")
                    else:
                        self._send_reply(from_number, f"You're not currently subscribed to {TARGET_GPU} stock alerts.")

                else:
                    self._send_reply(from_number, f"To subscribe to {TARGET_GPU} stock alerts, reply with '{SUBSCRIBE_KEYWORD}'. To unsubscribe, reply with '{UNSUBSCRIBE_KEYWORD}'.")

            # Update the last message date we processed
            if messages:
                self.state_manager.update_last_message_date(messages[0].date_created.isoformat())

            logging.info(f"Processed {processed_count} new messages")

        except TwilioRestException as e:
            logging.error(f"Twilio API error: {e}")
        except Exception as e:
            logging.error(f"Error checking for subscription messages: {e}")

    def _send_reply(self, to_number, message):
        """Send a reply message to a user"""
        if not self.client:
            logging.error("SMS client not initialized. Cannot send reply.")
            return False

        try:
            reply = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logging.info(f"Sent reply to {to_number}: {message}")
            return True
        except Exception as e:
            logging.error(f"Error sending reply to {to_number}: {e}")
            return False
