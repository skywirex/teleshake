#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
import config as config

API = config.API
WalletURL = "http://x:{}@127.0.0.1:12039/wallet/".format(API)
WalletID = config.WalletID
Account = config.Account

# Get Balance
def getBalance (account):
    url = WalletURL + WalletID + "/balance"
    params = (('account', account),)
    response = requests.get(url, params=json.dumps(params))
    return response.json ()

# Get Account Information
def getAccountInfo ():
    url = WalletURL + WalletID + "/account/" + Account
    response = requests.get(url)
    return response.json ()

# Get Wallet Names
def getWalletNames ():
    url = WalletURL + WalletID + "/name"
    response = requests.get(url)
    return response.json ()

# Get Wallet Names Own
def getWalletOwnNames ():
    url = WalletURL + WalletID + "/name"
    params = {'own': 'true',}
    response = requests.get(url, params=params)
    return response.json ()

# Get Wallet Name
def getWalletName (name):
    url = WalletURL + WalletID + "/name" + name
    response = requests.get(url)
    return response.json ()

# Get Wallet Auctions
def getWalletAuctions ():
    url = WalletURL + WalletID + "/auction"
    response = requests.get(url)
    return response.json ()

# Get Wallet Auction by Name
def getWalletAuctionsName (name):
    url = WalletURL + WalletID + "/auction" + name
    response = requests.get(url)
    return response.json ()

# Get Wallet Bids https://hsd-dev.org/api-docs/?shell--curl#get-wallet-bids
def getWalletBids ():
    url = WalletURL + WalletID + "/bid"
    params = (('own', True),)
    response = requests.get(url, params=json.dumps(params))
    return response.json ()

# Get Wallet Bids by Name
def getWalletBidsName (name):
    url = WalletURL + WalletID + "/bid/" + name
    params = (('own', False),)
    response = requests.get(url, params=json.dumps(params))
    return response.json ()

# Get Wallet Reveals
def getWalletReveals ():
    url = WalletURL + WalletID + "/reveal"
    params = (('own', False),)
    response = requests.get(url, params=json.dumps(params))
    return response.json ()

# Send OPEN
def sendOPEN (passphrase, name):
    url = WalletURL + WalletID + "/open"
    data = {"passphrase": passphrase, "name": name, "broadcast": True, "sign": True}
    response = requests.post(url, data=json.dumps(data))
    return response.json()

# Send BID https://hsd-dev.org/api-docs/?shell--curl#send-bid
def sendBID (passphrase, name, bid, lockup):
    url = WalletURL + WalletID + "/bid"
    data = {"passphrase": passphrase, "name": name, "broadcast": True, "sign": True,"bid": bid, "lockup": lockup}
    response = requests.post(url, data=json.dumps(data))
    return response.json()

# Send REVEAL https://hsd-dev.org/api-docs/?shell--curl#send-reveal
def sendREVEAL (passphrase, name):
    url = WalletURL + WalletID + "/reveal"
    data = {"passphrase": passphrase, "name": name, "broadcast": True, "sign": True}
    response = requests.post(url, data=json.dumps(data))
    return response.json ()

# Send REDEEM https://hsd-dev.org/api-docs/?shell--curl#send-redeem
def sendREDEEM (passphrase, name = None):
    url = WalletURL + WalletID + "/redeem"
    data = {"passphrase": passphrase, "name": name, "broadcast": True, "sign": True}
    response = requests.post(url, data=json.dumps(data))
    return response.json ()

# Send REDEEM https://hsd-dev.org/api-docs/?shell--curl#send-redeem
def sendUPDATE (passphrase, name, utype, key, value):
    url = WalletURL + WalletID + "/update"
    data = {"passphrase": passphrase,"name": name, "broadcast": True, "sign": True, "data": {"records": [ {"type": utype, key: [value]} ]}}
    response = requests.post(url, data=json.dumps(data))
    return response.json ()

# Send RENEW https://hsd-dev.org/api-docs/#send-renew
def sendRENEW (passphrase, name = None):
    url = WalletURL + WalletID + "/renewal"
    data = {"passphrase": passphrase, "name": name, "broadcast": True, "sign": True}
    response = requests.post(url, data=json.dumps(data))
    return response.json ()