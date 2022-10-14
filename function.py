#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json 
import requests
import os
import config as config
import node as node
import wallet as wallet


##### END IMPORT #####

# Convert to dollarydoo
def todollarydoo (amount):
    value = amount*1000000
    return value

def tohns (amount):
    value = amount/1000000
    return value

##### CUSTOM NODE FUNCTION #####

### Export name and expire day to a json file in data folder

def names_until_expire():
    ### Get registered name and days until expire directly in your wallet
    names_in_wallet =  wallet.getWalletOwnNames ()
    registered_names_in_wallet = []
    daysUntilExpire = []
    for i in names_in_wallet:
        if i['registered'] == True:
            registered_names_in_wallet.append(i['name'])
            daysUntilExpire.append(i['stats']['daysUntilExpire'])
    ### Construct dictionary 
    names_until_expire = dict(zip(registered_names_in_wallet,daysUntilExpire))
    ### Export to json file
    file_names_until_expire = os.path.join('.','data','names_expired.json')
    with open(file_names_until_expire, 'w') as f_obj:
        json.dump(names_until_expire, f_obj, indent=4)
    return names_until_expire

def expire_in_days (number):
    file_names_until_expire = os.path.join('.','data','names_expired.json')
    with open(file_names_until_expire) as f_obj:
        names_until_expire = json.load(f_obj)
        expire_in_days = []
        for name in names_until_expire:
            if names_until_expire[name] < number:
                expire_in_days.append (name)
    return expire_in_days

##### CUSTOM WALLET FUNCTION #####

## REVEAL all names in the wallet if it is in reveal stage

def reveal_names_in_wallet ():
    names_in_wallet = wallet.getWalletNames ()
    reveal = []
    for name in names_in_wallet:
        if name['state'] == 'REVEAL':
             wallet.sendREVEAL (config.passphrase,name['name'])
             reveal.append(name['name'])
    return reveal

### Check if names in the wallet in BIDDING state
def show_bidding_names_in_wallet ():
    names_in_wallet = wallet.getWalletNames ()
    bidding = []
    for name in names_in_wallet:
        if name['state'] == 'BIDDING':
            bidding.append(name['name'])
    return bidding

## Renew names in the list based on specific expired days
def renew_names_in_list (days):
    names_to_be_renews = expire_in_days (days)
    renew = []
    for name in names_to_be_renews:
        wallet.sendRENEW (config.passphrase, name)
        renew.append(name)
    return renew

## Bid at specific block
def bid_at_block (block, name, bid_value, lockup_value):
    block_height = node.block_height()
    if  block_height == block:
        wallet.sendBID (config.passphrase, name, todollarydoo(bid_value), todollarydoo(lockup_value))
    return