#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json 
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys && Your own Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates():
    url = URL + "getUpdates"
    js = get_json_from_url(url)
    return js

def get_chat_id():
    chat_id = TELEGRAM_CHAT_ID
    return (chat_id)

def send_message(text, chat_id):
    url = "https://api.telegram.org/bot{}/".format(TELEGRAM_BOT_TOKEN) + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)