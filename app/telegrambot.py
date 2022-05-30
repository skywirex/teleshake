#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json 
import requests
import config as config

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
    chat_id = config.CHAT_ID
    return (chat_id)

def send_message(text, chat_id):
    url = config.URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)