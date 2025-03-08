# NVIDIA RTX 5090 Stock Checker

This repository monitors Newegg's website for RTX 5090 GPU availability and sends an SMS notification when it comes in stock.

## Features

- Checks Newegg's website every ~hour minutes using GitHub Actions
- Sends SMS notifications when the GPU becomes available
- Only alerts on state changes (unavailable → available) to avoid notification spam
- Uses GitHub Actions Cache to reliably maintain state between runs
- Uses Poetry for dependency management
- Simplified subscription system - anyone who texts your Twilio number gets notified
- Optional Twilio webhook for triggering checks when receiving SMS messages
- Docker support for consistent development and deployment environments

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
     - `TWILIO_MESSAGING_SERVICE_SID`: Your Messaging Service SID (if using Messaging Services)

4. **Enable GitHub Actions**
   - Go to the Actions tab and enable workflows

5. **Done!** The workflow will now run every hour to check stock status.

You can also manually trigger a check by going to the Actions tab and running the "Check NVIDIA GPU Stock" workflow.

## How It Works

1. The GitHub Action runs every 57 minutes
2. It uses GitHub's cache system to store and retrieve the previous stock state
3. The script checks Newegg's website for RTX 5090 availability
4. If the GPU is in stock and it was previously out of stock, an SMS is sent with Twilio to all subscribers
5. The new state is saved to the cache for the next run

## SMS Subscription System

The subscription system is very simple:

- Anyone who texts your Twilio number (for any reason) is automatically added as a subscriber
- Users can text `STOP` to unsubscribe (handled automatically by Twilio)
- No need for special commands - just text the number to get alerts!

## Setting Up Twilio Messaging Services (Recommended)

This project can use Twilio's Messaging Services for improved message deliverability and simpler opt-out handling.

1. **Create a Messaging Service in Twilio Console**
   - Log in to [Twilio Console](https://www.twilio.com/console)
   - Navigate to "Messaging" > "Services"
   - Click "Create Messaging Service"
   - Give it a name like "NVIDIA GPU Stock Checker"
   - Choose "Notifications, alerts, and updates" as the use case

2. **Add Your Phone Number to the Messaging Service**
   - In your new Messaging Service, click "Add Senders"
   - Select "Phone Number" as the sender type
   - Choose your Twilio phone number and click "Continue"

3. **Configure Advanced Opt-Out (Optional but Recommended)**
   - In your Messaging Service, find the "Opt-Out Management" section
   - Click "Enable Advanced Opt-Out"
   - You can customize confirmation messages that users receive when they text STOP

4. **Update Your Environment Variables**
   - Add `TWILIO_MESSAGING_SERVICE_SID` to your `.env` file with the SID of your new Messaging Service
   - The SID starts with "MG" and can be found in your Messaging Service dashboard

## Deploying the Twilio Webhook (Optional)

For a more responsive system, you can deploy the included `twilio_webhook.js` file as a Twilio Function. This will trigger a stock check whenever someone texts your Twilio number.

1. **Log in to your Twilio Console**
   - Go to [https://www.twilio.com/console](https://www.twilio.com/console)

2. **Navigate to Functions & Assets**
   - In the left sidebar, go to "Explore Products" > "Functions & Assets" > "Services"
   - Click "Create Service" and give it a name like "GPU-Stock-Checker"

3. **Create a new Function**
   - Click "Add" > "Add Function"
   - Path: `/webhook` (or any path you prefer)
   - Make sure the `repoOwner`, `repoName`, and `workflowId` are correct in the `twilio_webhook.js` file
   - Copy the contents of `twilio_webhook.js` into the function editor

4. **Configure Environment Variables**
   - Click on "Environment Variables" in the left sidebar
   - Add the following variables:
     - `GITHUB_TOKEN`: A GitHub personal access token with `workflow` permissions

5. **Deploy the Function**
   - Click "Deploy All" to deploy your function

6. **Configure your Twilio Phone Number**
   - Go to "Phone Numbers" > "Manage" > "Active numbers"
   - Click on your Twilio phone number
   - Under "Messaging", set the webhook for "A Message Comes In" to your Function URL
   - The URL should look like: `https://your-service-name-xxxx.twil.io/webhook`
   - Save your changes

Now, whenever someone texts your Twilio number, it will trigger the GitHub workflow to check stock status immediately.

## Using Docker (Recommended)

This project includes Docker support for consistent development and deployment environments. Docker handles all the dependencies, including Chrome/Chromium for web scraping.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Development with Docker Compose

1. **Clone the repository and navigate to it:**
   ```bash
   git clone https://github.com/yourusername/nvidia-gpu-stock-checker.git
   cd nvidia-gpu-stock-checker
   ```

2. **Create a `.env` file with your Twilio credentials:**
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=your_twilio_number
   TWILIO_MESSAGING_SERVICE_SID=your_messaging_service_sid
   ```

3. **Build and start the container:**
   ```bash
   docker-compose up --build
   ```

   This will run the check once and exit. To run on a schedule locally, uncomment the command line in `docker-compose.yml` that includes the while loop.

4. **For development with Visual Studio Code:**
   - Install the "Remote - Containers" extension
   - Open the command palette (F1) and select "Remote-Containers: Open Folder in Container..."
   - Select the project folder

   This will build the development container and give you a fully configured development environment with all dependencies installed.

### Running One-Off Checks with Docker

```bash
docker-compose run stock-checker
```

## Reducing Twilio Logging

By default, Twilio's HTTP client logs detailed information at the INFO level. If you want to reduce this logging and only see warnings and errors, add the following code to your `src/sms_notifier.py` file after the imports:

```python
# Set Twilio loggers to WARNING level to reduce verbose logging
logging.getLogger('twilio').setLevel(logging.WARNING)
```

## Twilio Cost Consideration

Twilio charges per SMS sent (approximately $0.0075 per SMS for US numbers). Since this script only sends notifications when the GPU changes from unavailable to available, costs should be minimal.

## Running Locally (without Docker)

If you want to test the script locally without Docker:

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
   TWILIO_MESSAGING_SERVICE_SID=your_messaging_service_sid
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

## Troubleshooting

- **No SMS Notifications**: Check your Twilio account balance and logs in the Twilio console
- **Script Not Running**: Verify GitHub Actions is enabled and check the workflow runs
- **Webhook Not Working**: Check the Twilio Function logs in the Twilio console
- **Docker Issues**: Make sure you have the latest Docker and Docker Compose versions installed
