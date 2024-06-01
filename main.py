#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests
import os
import telegrambot as telegram
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

## Import from folder hsapi
from hsapi import node
from hsapi import wallet
##### END IMPORT #####


# Keys
passphrase = os.getenv('passphrase')
Account = os.getenv('Account')

# Convert to dollarydoo
def todollarydoo (amount):
    value = amount*1000000
    return value

def tohns (amount):
    value = amount/1000000
    return value

#### GENERAL INFORMATION #####

block_height = node.block_height()
balance = wallet.getBalance (Account)
spendable_balance = tohns (balance['unconfirmed']-balance['lockedUnconfirmed'])
get_account_info = wallet.getAccountInfo ()
address = get_account_info["receiveAddress"]

message = "Current Handshake block is: {}".format(block_height) + "\n$HNS Balance: {}".format(spendable_balance) + "\n" + address
chat_id = telegram.get_chat_id()
telegram.send_message(message, chat_id)
#### GENERAL INFORMATION #####

##### BEGIN CUSTOM NODE FUNCTION #####

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
    file_names_until_expire = 'names_expired.json'
    with open(file_names_until_expire, 'w') as f_obj:
        json.dump(names_until_expire, f_obj, indent=4)
    return names_until_expire

def expire_in_days (number):
    file_names_until_expire = 'names_expired.json'
    with open(file_names_until_expire) as f_obj:
        names_until_expire = json.load(f_obj)
        expire_in_days = []
        for name in names_until_expire:
            if names_until_expire[name] < number:
                expire_in_days.append (name)
    return expire_in_days

##### END CUSTOM NODE FUNCTION #####


##### BEGIN CUSTOM WALLET FUNCTION #####

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
##### END CUSTOM WALLET FUNCTION #####

### Send telegram message
##### chat_id = telegram.get_chat_id()
reveal = reveal_names_in_wallet ()
if reveal != []:
    telegram.send_message("REVEALING:\n {}".format(reveal), chat_id)

bidding = show_bidding_names_in_wallet ()
if bidding != []:
    telegram.send_message("BIDDING:\n {}".format(bidding), chat_id)

#### Export name and expired day to a json file
names_until_expire()

#### find name expire in No. of days (for example 100)
days = 100
y = expire_in_days (days)
if y != []:
    telegram.send_message("Handshake name will be expired in {} days:".format(days) + "\n" "{}".format(y) + "\n", chat_id)

z = renew_names_in_list (days)
if z != []:
    telegram.send_message("Renewed names {}:".format(z) + "\n", chat_id)
else:
    telegram.send_message("There are no names to renew on the Handshake block {}".format(block_height) + "\n", chat_id)

#### Bid at specific block ####
# block = 77927
# name = "gdns"
# bid_value = 5
# lockup_value = 10

# x = bid_at_block (block, name, bid_value, lockup_value)

# if x != None:
#     message = "Biding name: {}".format(name) + "\n" + "Value: {}".format(bid_value) + "\n" + "Mask: {}".format(lockup_value) + "\n" + json.dumps(x, indent=4)
#     chat_id = telegram.get_chat_id()
#     telegram.send_message(message, chat_id)
    
#### Bid at specific block ####