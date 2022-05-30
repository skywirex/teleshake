#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
import function
import node as node
import wallet as wallet
import telegrambot as telegram
import config as config

# https://hsd-dev.org/api-docs/?shell--curl#introduction
# https://curl.trillworks.com/
# https://stackoverflow.com/questions/18810777/how-do-i-read-a-response-from-python-requests

#### GENERAL INFORMATION #####

block_height = node.block_height()
balance = wallet.getBalance (config.Account)
spendable_balance = function.tohns (balance['unconfirmed']-balance['lockedUnconfirmed'])
get_account_info = wallet.getAccountInfo ()
address = get_account_info["receiveAddress"]

message = "Current Handshake block is: {}".format(block_height) + "\n$HNS Balance: {}".format(spendable_balance) + "\n" + address
chat_id = telegram.get_chat_id()
telegram.send_message(message, chat_id)
#### GENERAL INFORMATION #####


reveal = function.reveal_names_in_wallet ()
bidding = function.show_bidding_names_in_wallet ()
        
### Send telegram message
##### chat_id = telegram.get_chat_id()
telegram.send_message("REVEALING:\n {}".format(reveal), chat_id)
telegram.send_message("BIDDING:\n {}".format(bidding), chat_id)

###test###
def names_until_expire():
    names_in_wallet =  wallet.getWalletOwnNames ()
    registered_names_in_wallet = []
    daysUntilExpire = []
    for i in names_in_wallet:
        if i['registered'] == True:
            registered_names_in_wallet.append(i['name'])
            daysUntilExpire.append(i['stats']['daysUntilExpire'])
    names_until_expire = dict(zip(registered_names_in_wallet,daysUntilExpire))
## export to json file
    file_names_until_expire = '../data/output_names_until_expire.json'
    with open(file_names_until_expire, 'w') as f_obj:
        json.dump(names_until_expire, f_obj, indent=4)
    return names_until_expire
print(names_until_expire())