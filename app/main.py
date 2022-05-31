#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
import function
import node as node
import wallet as wallet
import telegrambot as telegram
import config as config
##### END IMPORT #####

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

### Send telegram message
##### chat_id = telegram.get_chat_id()
reveal = function.reveal_names_in_wallet ()
if reveal != []:
    telegram.send_message("REVEALING:\n {}".format(reveal), chat_id)

bidding = function.show_bidding_names_in_wallet ()
if bidding != []:
    telegram.send_message("BIDDING:\n {}".format(bidding), chat_id)

#### Export name and expired day to a json file
x = function.names_until_expire()

#### find name expire in No. of days (for example 100)
days = 100
y = function.expire_in_days (days)
##### chat_id = telegram.get_chat_id()
telegram.send_message("Handshake name will be expired in {} days:".format(days) + "\n" "{}".format(y) + "\n", chat_id)

z = function.renew_names_in_list (days)

##### chat_id = telegram.get_chat_id()
telegram.send_message("Renewed names {}:".format(z) + "\n", chat_id)

#### Bid at specific block ####
block = 77927
name = "gdns"
bid_value = 5
lockup_value = 10

x = function.bid_at_block (block, name, bid_value, lockup_value)

if x != None:
    message = "Biding name: {}".format(name) + "\n" + "Value: {}".format(bid_value) + "\n" + "Mask: {}".format(lockup_value) + "\n" + json.dumps(x, indent=4)
    chat_id = telegram.get_chat_id()
    telegram.send_message(message, chat_id)
    
#### Bid at specific block ####