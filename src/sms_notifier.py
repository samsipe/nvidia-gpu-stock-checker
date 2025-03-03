import logging
from twilio.rest import Client

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, SMS_TO_NUMBER, TARGET_GPU, NVIDIA_URL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SMSNotifier:
    def __init__(self):
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.from_number = TWILIO_FROM_NUMBER
        self.to_number = SMS_TO_NUMBER

    def send_notification(self):
        """Send SMS notification that GPU is in stock"""
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            logging.error("SMS configuration is incomplete. Check your environment variables.")
            return False

        try:
            client = Client(self.account_sid, self.auth_token)

            # Create and send message
            message = client.messages.create(
                body=f"🚨 ALERT: {TARGET_GPU} IS NOW IN STOCK! Check stock immediately: {NVIDIA_URL}",
                from_=self.from_number,
                to=self.to_number
            )

            logging.info(f"SMS notification sent with SID: {message.sid}")
            return True

        except Exception as e:
            logging.error(f"Error sending SMS notification: {e}")
            return False
