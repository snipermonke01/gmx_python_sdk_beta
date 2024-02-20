#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 20:59:48 2023

@author: snipermonke01
"""

import json
import os

from web3 import Web3

from .gmx_utils import create_connection
from .gmx_utils import base_dir, get_config


def check_if_approved(
        chain: str,
        spender: str,
        token_to_approve: str,
        amount_of_tokens_to_spend: int,
        approve: bool):
    """
    For a given chain, check if a given amount of tokens is approved for spend by a contract, and
    approve is passed as true

    Parameters
    ----------
    chain : str
        arbitrum or avalanche.
    spender : str
        contract address of the requested spender.
    token_to_approve : str
        contract address of token to spend.
    amount_of_tokens_to_spend : int
        amount of tokens to spend in expanded decimals.
    approve : bool
        Pass as True if we want to approve spend incase it is not already.

    Raises
    ------
    Exception
        Insufficient balance or token not approved for spend.

    """

    config = get_config()
    connection = create_connection(chain=chain)

    spender_checksum_address = Web3.to_checksum_address(spender)

    # User wallet address will be taken from config file
    user_checksum_address = Web3.to_checksum_address(config['user_wallet_address'])

    token_checksum_address = Web3.to_checksum_address(token_to_approve)

    token_contract_abi = json.load(open(os.path.join(base_dir,
                                                     'contracts',
                                                     'v2',
                                                     'token_approval.json')))
    token_contract_obj = connection.eth.contract(address=token_to_approve,
                                                 abi=token_contract_abi)

    # TODO - for AVAX support this will need to incl WAVAX address
    if token_checksum_address == "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1":
        try:
            balance_of = connection.eth.getBalance(user_checksum_address)
        except AttributeError:
            balance_of = connection.eth.get_balance(user_checksum_address)

    else:
        balance_of = token_contract_obj.functions.balanceOf(user_checksum_address).call()

    if balance_of < amount_of_tokens_to_spend:
        raise Exception("Insufficient balance!")

    amount_approved = token_contract_obj.functions.allowance(
        user_checksum_address,
        spender_checksum_address
    ).call()

    print("Checking coins for approval..")
    if amount_approved < amount_of_tokens_to_spend and approve:

        print('Approving contract "{}" to spend {} tokens belonging to token address: {}'.format(
            spender_checksum_address, amount_of_tokens_to_spend, token_checksum_address))

        nonce = connection.eth.get_transaction_count(user_checksum_address)

        arguments = spender_checksum_address, amount_of_tokens_to_spend
        raw_txn = token_contract_obj.functions.approve(
            *arguments
        ).build_transaction({
            'value': 0,
            'chainId': 42161,
            'gas': 4000000,
            'maxFeePerGas': Web3.to_wei('0.1', 'gwei'),
            'maxPriorityFeePerGas': Web3.to_wei('0.1', 'gwei'),
            'nonce': nonce})

        signed_txn = connection.eth.account.sign_transaction(raw_txn,
                                                             config['private_key'])
        tx_hash = connection.eth.send_raw_transaction(signed_txn.rawTransaction)

        print("Txn submitted!")
        print("Check status: https://arbiscan.io/tx/{}".format(tx_hash.hex()))

    if amount_approved < amount_of_tokens_to_spend and not approve:
        raise Exception("Token not approved for spend, please allow first!")

    print('Contract "{}" approved to spend {} tokens belonging to token address: {}'.format(
        spender_checksum_address, amount_of_tokens_to_spend, token_checksum_address))
    print("Coins Approved for spend!")


if __name__ == "__main__":

    chain = 'arbitrum'
    spender = "0x7452c558d45f8afC8c83dAe62C3f8A5BE19c71f6"
    token_to_approve = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    amount_of_tokens_to_spend = 1
    approve = True

    test = check_if_approved(chain,
                             spender,
                             token_to_approve,
                             amount_of_tokens_to_spend,
                             approve)
