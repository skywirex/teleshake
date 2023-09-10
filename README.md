# Teleshake - User Guide

## Update Python

To ensure your Teleshake program runs smoothly, you need to update Python and install necessary packages. Follow these steps:

1. Update Python to Python 3 and install pip3:
   ```bash
   update-alternatives --install /usr/bin/python python /usr/bin/python3 1
   apt install python3-pip
   ```

2. Install the 'requests' package using pip3:
   ```bash
   pip3 install requests
   ```

## Configure Your Program

Before you can use Teleshake, you need to configure it properly. Follow these steps:

1. **Run hsd in a Docker container and test the endpoint:**
   Use the following command to test the hsd endpoint:
   ```bash
   curl http://x:<your-api>0@127.0.0.1:12037
   ```

2. **Prepare the following information:**
   ```bash
   API = "<your-API>"
   passphrase = "<your-pass>"
   WalletID = "<your-wallet-ID>"
   Account = "default"
   ```

3. Modify the information in the `config.py` file according to the details you prepared.

4. For sending messages to Telegram, you'll need the following information:
   ```bash
   TOKEN = "<your-token>"
   CHAT_ID = "<your-chat-id>"
   URL = "https://api.telegram.org/bot{}/".format(TOKEN)
   ```

   Update the `config.py` file with this information.

## Setting up Cron

To automate Teleshake and run it at specific intervals, you can use the cron job scheduler. Follow these steps:

1. Open your crontab file for editing:
   ```bash
   crontab -e
   ```

2. Add the following line at the end of the file to run Teleshake every hour:
   ```bash
   0 * * * * /root/teleshake/run-main.sh
   ```

   This will execute Teleshake's main script every hour.