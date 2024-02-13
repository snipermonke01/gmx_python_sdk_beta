#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 11:23:05 2023

@author: snipermonke01
"""

from .keys import decrease_order_gas_limit_key, increase_order_gas_limit_key, \
    execution_gas_fee_base_amount_key, execution_gas_fee_multiplier_key, single_swap_gas_limit_key,\
    swap_order_gas_limit_key

from .gmx_utils import apply_factor, get_datastore_contract, create_connection


def get_execution_fee(gas_limits, estimated_gas_limit, gas_price):

    base_gas_limit = gas_limits['estimated_fee_base_gas_limit'].call()
    multiplier_factor = gas_limits['estimated_fee_multiplier_factor'].call()
    adjusted_gas_limit = base_gas_limit + apply_factor(estimated_gas_limit.call(),
                                                       multiplier_factor)

    return adjusted_gas_limit * gas_price


def get_gas_limits(datastore_object):
    gas_limits = {
        "deposit_single_token": None,
        "deposit_multi_token": None,
        "withdraw_multi_token": None,
        "single_swap": datastore_object.functions.getUint(single_swap_gas_limit_key()),
        "swap_order": datastore_object.functions.getUint(swap_order_gas_limit_key()),
        "increase_order": datastore_object.functions.getUint(increase_order_gas_limit_key()),
        "decrease_order": datastore_object.functions.getUint(decrease_order_gas_limit_key()),
        "estimated_fee_base_gas_limit": datastore_object.functions.getUint(
            execution_gas_fee_base_amount_key()),
        "estimated_fee_multiplier_factor": datastore_object.functions.getUint(
            execution_gas_fee_multiplier_key())}

    return gas_limits


if __name__ == "__main__":

    chain = 'arbitrum'
    connection = create_connection(chain=chain)
    datastore_object = get_datastore_contract(chain)
    gas_limits = get_gas_limits(datastore_object)
    gas_price = connection.eth.gas_price
    execution_fee = int(get_execution_fee(gas_limits, gas_limits['increase_order'], gas_price))
