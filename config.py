import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GPU details
TARGET_GPU = os.getenv("TARGET_GPU", "GeForce RTX 5090")
# TARGET_GPU = "GeForce RTX 4090" # testing

# URL to check
NVIDIA_URL = os.getenv("NVIDIA_URL", "https://www.newegg.com/p/pl?N=100007709%20601469153%2050001314%2050001312%2050001315%208000")
# NVIDIA_URL = "https://www.newegg.com/p/pl?N=100007709%2050001314%2050001312%2050001315%20601408874%208000" # testing

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

# State file to track availability and subscribers
STATE_FILE = "gpu_availability.json"
