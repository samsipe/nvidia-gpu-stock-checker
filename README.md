# NVIDIA RTX 5090 Stock Checker

This repository monitors Newegg's website for RTX 5090 GPU availability and sends an SMS notification when it comes in stock.

## Features

- Checks Newegg's website every ~hour minutes using GitHub Actions
- Sends SMS notifications when the GPU becomes available
- Only alerts on state changes (unavailable → available) to avoid notification spam
- Uses GitHub Actions Cache to reliably maintain state between runs
- Uses Poetry for dependency management

## Setup Instructions

1. **Create a Twilio Account**
   - Sign up at [https://www.twilio.com/](https://www.twilio.com/)
   - Get a Twilio phone number (this will be your FROM number)
   - Note your Account SID and Auth Token from the Twilio dashboard

2. **Fork this repository**

3. **Set up secrets in your GitHub repository:**
   - Go to Settings > Secrets and variables > Actions
   - Add the following secrets:
     - `TWILIO_ACCOUNT_SID`: Your Twilio account SID
     - `TWILIO_AUTH_TOKEN`: Your Twilio auth token
     - `TWILIO_FROM_NUMBER`: Your Twilio phone number (format: +1XXXXXXXXXX)
     - `SMS_TO_NUMBER`: Your personal phone number to receive alerts (format: +1XXXXXXXXXX)

4. **Enable GitHub Actions**
   - Go to the Actions tab and enable workflows

5. **Done!** The workflow will now run every hour to check stock status.

You can also manually trigger a check by going to the Actions tab and running the "Check NVIDIA GPU Stock" workflow.

## How It Works

1. The GitHub Action runs every 57 minutes
2. It uses GitHub's cache system to store and retrieve the previous stock state
3. The script checks Newegg's website for RTX 5090 availability
4. If the GPU is in stock and it was previously out of stock, an SMS is sent with Twilio
5. The new state is saved to the cache for the next run

## Twilio Cost Consideration

Twilio charges per SMS sent (approximately $0.0075 per SMS for US numbers). Since this script only sends notifications when the GPU changes from unavailable to available, costs should be minimal.

## Running Locally (for testing)

If you want to test the script locally:

1. **Make sure Poetry is installed:**
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies:**
   ```
   poetry install
   ```

3. **Create a `.env` file in the root directory with:**
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=your_twilio_number
   SMS_TO_NUMBER=your_personal_number
   ```

4. **Run the script:**
   ```
   poetry run python main.py
   ```

## Customization

Edit the [config.py](config.py) file to change:
- Target GPU model `TARGET_GPU`
- Monitoring URL `NVIDIA_URL` (link to a product search on Newegg)
- This can be modified to check the stock of any item on Newegg
