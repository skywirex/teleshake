#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import ../config.py
import config

API = config.API
NodeURL = "http://x:{}@localhost:12037/".format(API)

def block_height ():
    url = NodeURL
    response = requests.get(url)
    thisdict = response.json()
    return thisdict['chain']['height']

def days_until_expire (name):
    url = NodeURL
    data = { "method": "getnameinfo", "params": [name] }
    response = requests.post(url, data = json.dumps(data))
    thisdict = response.json()
    return thisdict['result']['info']['stats']['daysUntilExpire']