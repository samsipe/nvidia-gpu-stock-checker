import logging
from datetime import datetime, timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient
import time

from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    TWILIO_MESSAGING_SERVICE_SID,
    TARGET_GPU,
    NVIDIA_URL,
)
from nvidia_gpu_stock_checker.state_manager import StateManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Set Twilio loggers to WARNING level to reduce verbose logging
logging.getLogger("twilio").setLevel(logging.WARNING)


class SMSNotifier:
    def __init__(self):
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.from_number = TWILIO_FROM_NUMBER
        self.messaging_service_sid = TWILIO_MESSAGING_SERVICE_SID
        self.state_manager = StateManager()

        # Initialize Twilio client
        if all(
            [
                self.account_sid,
                self.auth_token,
                self.from_number,
                self.messaging_service_sid,
            ]
        ):
            # Create a custom HTTP client with reduced logging
            http_client = TwilioHttpClient()
            self.client = Client(
                self.account_sid, self.auth_token, http_client=http_client
            )
        else:
            logging.error(
                "SMS configuration is incomplete. Check your environment variables."
            )
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
                    # Create and send message using the Messaging Service
                    message = self.client.messages.create(
                        body=f"🚨 ALERT: {TARGET_GPU} IS NOW IN STOCK! {NVIDIA_URL}",
                        from_=self.from_number,
                        messaging_service_sid=self.messaging_service_sid,
                        to=to_number,
                    )
                    logging.info(
                        f"SMS notification sent to {to_number} with SID: {message.sid}"
                    )
                    successful_sends += 1
                except TwilioRestException as e:
                    logging.error(f"Twilio error sending SMS to {to_number}: {e}")
                except Exception as e:
                    logging.error(f"Error sending SMS to {to_number}: {e}")

            logging.info(
                f"Notification sent to {successful_sends}/{len(subscribers)} subscribers"
            )
            return successful_sends > 0

        except Exception as e:
            logging.error(f"Error sending notifications: {e}")
            return False

    def get_subscribers(self):
        """Return the list of subscribers"""
        return self.state_manager.get_subscribers()

    def check_for_subscription_messages(self):
        """Check for new incoming messages and add senders as subscribers"""
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
                if (
                    last_message_date
                    and message.date_created.isoformat() <= last_message_date
                ):
                    break

                processed_count += 1
                from_number = message.from_

                # Add anyone who texts as a subscriber
                self.state_manager.add_subscriber(from_number)
                logging.debug(f"Added/confirmed subscriber: {from_number}")

                # Send confirmation message
                try:
                    response_message = self.client.messages.create(
                        body=f"You're subscribed for {TARGET_GPU} alerts. We'll text you when it's in stock.",
                        from_=self.from_number,
                        messaging_service_sid=self.messaging_service_sid,
                        to=from_number,
                    )
                    time.sleep(1)  # Give Twilio time to process the message
                    response_message = self.client.messages(
                        response_message.sid
                    ).fetch()
                    if response_message.error_code == 21610:
                        logging.info(
                            f"User {from_number} has opted out, removing from subscribers"
                        )
                        self.state_manager.remove_subscriber(from_number)
                    else:
                        logging.info(
                            f"Sent confirmation to {from_number} with SID: {response_message.sid}"
                        )
                except TwilioRestException as e:
                    logging.error(
                        f"Twilio error sending confirmation to {from_number}: {e}"
                    )
                except Exception as e:
                    logging.error(f"Error sending confirmation to {from_number}: {e}")

            # Update the last message date we processed
            if messages:
                self.state_manager.update_last_message_date(
                    messages[0].date_created.isoformat()
                )

            logging.info(f"Processed {processed_count} new messages")

        except TwilioRestException as e:
            logging.error(f"Twilio API error: {e}")
        except Exception as e:
            logging.error(f"Error checking for subscription messages: {e}")
