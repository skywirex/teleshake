# TeleShake

## Automatic Handshake Domain Renewal + Telegram Alerts

### Features

- TeleShake automatically checks your Handshake domains and renews them before expiration.
- Notifications are sent directly to your Telegram chat.
- The default Docker image supports two architectures: amd and arm64.

### Note

- This tool is provided “as is.” Use it at your own risk.

![TeleShake bot](https://pub-b731809282d4443bba205fbf4c8ae4ee.r2.dev/e152dd199ec6f4e1e067486d615f6d4f.png)

---

## Prerequisites

### **Docker**
Make sure Docker is installed on your system.

### **Telegram Bot**

You need:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Create a bot Telegram Bot using **@BotFather**, then retrieve your chat ID.  
More detailed guide: [here](https://skywirex.com/create-telegram-bot-get-chat-id/)

---

## Setup TeleShake

### **1. Run `hsd` Daemon**

You may change the values of `api-key` and `wallet-api-key` as needed.

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
  --api-key=api \
  --wallet-http-host=0.0.0.0 \
  --wallet-api-key=api
````
Check endpoint

```bash
curl http://x:api@127.0.0.1:12037/
```

---

### **2. Import Wallet & Rescan**

Temporarily disable history to prevent exposing the mnemonic:

```bash
set +o history
```

Import your seed to the wallet (change `imported_wallet` if needed):

```bash
curl http://x:api@127.0.0.1:12039/wallet/imported_wallet \
  -X PUT \
  --data '{"passphrase":"secretpass123", "mnemonic":"<words words words...words>"}' \
  &&
set -o history 
```

Check imported wallets:

```bash
curl http://x:api@127.0.0.1:12039/wallet
```
Rescan wallet from a specific block height:

```bash
curl http://x:api@127.0.0.1:12039/rescan \
  -X POST \
  --data '{"height": 50}'
```

---

### **3. Create `config.json`**

Create `teleshake` folder and `config.json` file. Modify values to match your setup.

```bash
mkdir -p $HOME/docker/teleshake
```
```bash
cat > $HOME/docker/teleshake/config.json << 'EOF'
{
  "WALLET_API": "api",
  "WALLET_ADDRESS": "127.0.0.1",
  "WALLET_PORT": 12039,
  "WALLET_ID": "primary",
  "WALLET_PASSPHRASE": "secretpass123",
  "NODE_API_KEY": "api",
  "NODE_HOST": "127.0.0.1",
  "NODE_PORT": 12037,
  "RENEWAL_THRESHOLD_DAYS": 60,
  "TELEGRAM_BOT_TOKEN": "your_bot_token",
  "TELEGRAM_CHAT_ID": "your_chat_id"
}
EOF
```
---

### **4. Run TeleShake (Docker)**

```bash
docker run -d \
  --name teleshake \
  --restart unless-stopped \
  --network host \
  -v $HOME/docker/teleshake/config.json:/app/config.json \
  skywirex/teleshake:v0.2.0
```

⏱ **Default check interval:** 1 hour ~ 3600s

You can change it by adding `-e LOOP_SECONDS=3600`

---

### **5. Check Services**

```bash
docker ps -a
```

```bash
docker logs teleshake -f
```

---

### **6. Stop and Remove**

```bash
docker rm teleshake -f
docker rm hsd -f
```


## Deploy with Docker Compose

Create directory:

```bash
mkdir -p $HOME/docker/teleshake
```

Create `compose.yml` and `config.json` inside the folder:

```yaml
---
services:
  hsd:
    image: handshakeorg/hsd:8.0.0
    container_name: hsd
    network_mode: host
    restart: unless-stopped
    volumes:
      - $HOME/.hsd:/root/.hsd
    command: >
      --network main
      --spv
      --http-host 0.0.0.0
      --api-key=api
      --wallet-http-host=0.0.0.0
      --wallet-api-key=api

  teleshake:
    image: skywirex/teleshake:v0.2.0
    container_name: teleshake
    network_mode: host
    depends_on:
      - hsd
    restart: unless-stopped
    volumes:
      - $HOME/docker/teleshake/config.json:/app/config.json
    environment:
      - LOOP_SECONDS=3600   # Change as needed
```

Start services:

```bash
docker compose up -d
```

---

## Project Structure

```
teleshake/
├── .github/
├── .gitignore
├── Dockerfile
├── LICENSE
├── README.md
├── entrypoint.sh             
├── main.py                   
├── requirements.txt
├── bot_telegram.py
├── utils.py
├── api/                      # Handshake node & wallet API for future development
├── img/                      # Images and assets
├── sample/                   # Example configs
└── scripts/
    └── teleshake.sh          # Infinite loop
```

---

## Reference 

* [handywrapper](https://github.com/skunk-ink/handywrapper) 

## Donation

🙏 If this tool helps you:

* **HNS:** `hs1qwrsfl8vkjqxfdncfn00dtzvpcdcj3rlj70zg3m`
* **ETH (EVM):** `0x548Dd6E1794a13BaeFd9cC16fB2340A6be8680d6`