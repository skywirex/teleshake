## teleshake


### Update python

```
update-alternatives --install /usr/bin/python python /usr/bin/python3 1
apt install python3-pip
pip3 install requests
```

### Config your program

##### 1. Run hsd in a docker container and test endpoint

```
curl http://x:<your-api>0@127.0.0.1:12037
```

##### 2. Prepare the following information:

```
API = "<your-API>"
passphrase = "<your-pass>"
WalletID = "<your-wallet-ID>"
Account = "default"
```

Modify that information in `config.py`

##### 3. For sending the message to telegram 

```
TOKEN = "<your-token>"
CHAT_ID = "<your-chat-id>"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
``` 

### Setting crontab 

Run `crontab -e` and put the following at the end of file

```
0 * * * * /root/teleshake/main.py
```