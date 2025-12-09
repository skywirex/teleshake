## Prerequisites

### Docker
Ensure Docker is installed on your system.

### Telegram Bot
A Telegram bot must be created via [BotFather](https://t.me/BotFather) to get a `TELEGRAM_BOT_TOKEN`, and you need a `TELEGRAM_CHAT_ID` for the target chat.

#### Create a Telegram Bot:
1. Open Telegram and start a chat with `@BotFather`.
2. Send `/newbot`, follow the instructions, and record the bot token (e.g., `123456789:AAF...`).

#### Obtain the Chat ID:
1. Add the bot to a group or send it a direct message.
2. Send a test message, then retrieve the chat ID using:

```bash
curl https://api.telegram.org/bot<your_bot_token>/getUpdates
```

3. In the JSON response, find `"chat":{"id":<chat_id>}` (e.g., `123456789` or `-123456789` for groups).
4. Alternatively, use `@GetIDsBot` to get the chat ID easily.

#### Test the Bot:
Send a manual test message to verify setup:

```bash
curl -X POST "https://api.telegram.org/bot<your_bot_token>/sendMessage" -d "chat_id=<your_chat_id>&text=Test message"
```

### Handshake Node (hsd)
A running `hsd` instance (with wallet enabled) is required, as `main.py` interacts with it via `HSD_API.py` and `WALLET_API.py`. Ensure it’s configured with API keys and accessible at the addresses/ports specified in `.env`.

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
  "WALLET_API": "skywirex",
  "WALLET_ADDRESS": "127.0.0.1",
  "WALLET_PORT": 12039,
  "WALLET_ID": "primary",
  "WALLET_PASSPHRASE": "your_secure_passphrase",
  "NODE_API_KEY": "skywirex",
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
├── .github/
│   └── workflows/                # GitHub Actions
├── .gitignore
├── Dockerfile                    # Pure script-based, no OpenRC, no Supervisor
├── LICENSE
├── README.md
├── entrypoint.sh                 # just runs teleshake.sh
├── main.py                       # Core logic
├── requirements.txt
├── bot_telegram.py
├── utils.py
├── api/                          # Handshake node & wallet API clients
├── img/                          # Images for README, etc.)
├── sample/                       # (example configs)
└── scripts/
    └── teleshake.sh              # The only thing that runs forever
                                  # → loop + sleep + LOOP_SECONDS env var
```