## Prerequisites

### Python Installed
Ensure Python 3.7+ is installed on your system. Check with:

```bash
python3 --version
```

If not installed, download it from [python.org](https://www.python.org/) or use a package manager (e.g., `apt`, `brew`).

### Handshake Node (hsd)
A running `hsd` instance (with wallet enabled) is required, as `main.py` interacts with it via `HSD_API.py` and `WALLET_API.py`. Ensure it’s configured with API keys and accessible at the addresses/ports specified in `.env`.

### Telegram Bot
A Telegram bot must be created via [BotFather](https://t.me/BotFather) to get a `TELEGRAM_BOT_TOKEN`, and you need a `TELEGRAM_CHAT_ID` for the target chat.

## Step-by-Step Instructions to Run `main.py`

### 1. Set Up the Environment
Navigate to the project directory:

```bash
cd /path/to/project
```

### 2. Install Dependencies
Ensure `requirements.txt` includes all necessary packages. Here’s a sample `requirements.txt` based on the script’s needs:

```
requests
python-dotenv
```

Install the dependencies:

```bash
pip3 install -r requirements.txt
```

- `requests`: For HTTP requests in `bot.py`, `HSD_API.py`, and `WALLET_API.py`.
- `python-dotenv`: To load `.env` variables.

If `requirements.txt` is missing or incomplete, create/update it with the above content and run the command.

### 3. Configure `.env`
Verify your `.env` file contains all required variables. Example:

```
WALLET_API=your_wallet_api_key
WALLET_ADDRESS=127.0.0.1
WALLET_PORT=12039
WALLET_ID=primary
WALLET_PASSPHRASE=your_secure_passphrase
WALLET_MNEMONIC=your_12_or_24_word_mnemonic
NODE_API_KEY=your_node_api_key
NODE_HOST=127.0.0.1
NODE_PORT=12037
RENEWAL_THRESHOLD_DAYS=30
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Replace placeholders (e.g., `your_wallet_api_key`) with actual values.

Ensure `hsd` is running at `NODE_HOST:NODE_PORT` and the wallet at `WALLET_ADDRESS:WALLET_PORT`.

### 4. Verify `hsd` and Wallet Are Running
Start your Handshake node with wallet support if not already running:

```bash
hsd --api-key=your_node_api_key --wallet-api-key=your_wallet_api_key
```

Use `--testnet` if testing on the test network.

Confirm it’s accessible (e.g., via `curl http://127.0.0.1:12037` with the API key).

### 5. Run `main.py`
Run the script in the foreground to test it:

```bash
python3 main.py
```

**Expected Output:** It will check the wallet, fetch names, renew if needed, send a Telegram message, and sleep for `LOOP_PERIOD_SECONDS` (e.g., 3600 seconds). Example:

```
Wallet 'primary' already exists
Names data saved to wallet_names.json
Notification sent. Sleeping for 3600 seconds...
```

### 6. Run in the Background (Optional)
Since `main.py` runs in a loop, you’ll likely want it to persist. Use one of these methods:

#### Using `nohup` (Linux/macOS):
```bash
nohup python3 main.py > output.log 2>&1 &
```
Logs output to `output.log`.

Check the process with `ps aux | grep main.py`.

#### Using `screen` (Linux/macOS):
```bash
screen -S handshake-bot
python3 main.py
```
Detach with `Ctrl+A, D`. Reattach with `screen -r handshake-bot`.

#### As a `systemd` Service (Linux, recommended for production):
Create `/etc/systemd/system/handshake-bot.service`:

```
[Unit]
Description=Handshake Wallet Renewal Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/project/main.py
WorkingDirectory=/path/to/project
Restart=always
User=your_username

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl enable handshake-bot
sudo systemctl start handshake-bot
```

Check status:
```bash
sudo systemctl status handshake-bot
```

### 7. Monitor Execution

#### Telegram
Verify you receive messages like:

```
Handshake Wallet Update (2025-03-14 10:00:00)
<b>Wallet/Node Info:</b>
Block Height: 268271
Account: primary
Balance: 123.5 HNS
Address: <a href='hs1q1234567890abcdefxyz'>hs1q12...fxyz</a>

<b>Renewals:</b>
No renewals
```

#### Console/Log
Check `output.log` (if using `nohup`) or the terminal for errors.

### 8. Stop the Script (If Needed)

#### Foreground
Press `Ctrl+C`.

#### Background (`nohup`)
Find the PID (`ps aux | grep main.py`) and kill it:

```bash
kill -9 <pid>
```

#### `systemd`
```bash
sudo systemctl stop handshake-bot
```
### Docker

#### **hsd daemon**

```bash
docker run -d \
  --name hsd \
  --network host \
  --restart unless-stopped \
  -v $HOME/.hsd:/root/.hsd \
  handshakeorg/hsd:8.0.0 \
  --network main \
  --spv \
  --http-host 0.0.0.0 \
  --api-key=skywirex \
  --wallet-http-host=0.0.0.0 \
  --wallet-api-key=skywirex
```

#### **Create config.json file**

Here is the **CLI command to create the directory and the `config.json` file** inside `$HOME/docker/teleshake/` with the sample content. Modify it based on your infor.

```bash
mkdir -p $HOME/docker/teleshake

cat > $HOME/docker/teleshake/config.json << 'EOF'
{
  "WALLET_API": "your_wallet_api_key",
  "WALLET_ADDRESS": "127.0.0.1",
  "WALLET_PORT": 12039,
  "WALLET_ID": "primary",
  "WALLET_PASSPHRASE": "your_secure_passphrase",
  "NODE_API_KEY": "your_node_api_key",
  "NODE_HOST": "127.0.0.1",
  "NODE_PORT": 12037,
  "RENEWAL_THRESHOLD_DAYS": 60,
  "TELEGRAM_BOT_TOKEN": "your_bot_token",
  "TELEGRAM_CHAT_ID": "your_chat_id",
}
EOF
```

#### **teleshake**

```bash
docker run -d \
  --name teleshake \
  --network host \
  -v $HOME/docker/teleshake/config.json:/app/config.json \
  skywirex/teleshake:latest
```
### Project Structure

```
teleshake/
├── api/                  # Handshake node & wallet API clients
│   ├── HSD_API.py
│   └── WALLET_API.py
├── img/                  # Image-related assets (added at initial commit)
├── sample/               # Sample configs/scripts (recently updated)
└── supervisor/
│   ├── supervisord.conf   # main config
│   └── conf.d/
│        └── teleshake.conf  # your program
├── .gitignore            # Git ignore rules
├── Dockerfile            # Docker setup (modified recently)
├── LICENSE               # Apache-2.0 license
├── README.md             # Documentation (Docker section added)
├── bot_telegram.py       # Telegram bot integration
├── main.py               # Entry point (runs a single cycle)
├── requirements.txt      # Python dependencies
└── utils.py              # Helper functions
```