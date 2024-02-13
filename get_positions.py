#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 23:00:34 2024

@author: snipermonke01
"""

from scripts.v2.get_open_positons import GetOpenPositons
from scripts.v2.gmx_utils import get_config, find_dictionary_by_key_value, get_tokens_address_dict


def get_positions(chain: str, address: str = None):
    """
    Get open positions for an address on a given network. If address is not passed it will take the
    address from the users config file. 

    Parameters
    ----------
    chain : str
        arbitrum or avalanche.
    address : str, optional
        address to fetch open positions for. The default is None.

    Returns
    -------
    positions : dict
        dictionary containing all open positions.

    """

    # TODO - put in a catch here if address passed is None and we dont have one in config file
    if address is None:
        address = get_config()['user_wallet_address']

    positions = GetOpenPositons(chain=chain).get_positions(address=address)

    if len(positions) > 1:
        print("Open Positions for {}:".format(address))
        for key in positions.keys():
            print(key)

    return positions


def transform_open_position_to_order_parameters(
    chain: str,
    positions: dict,
    market_symbol: str,
    is_long: bool,
    slippage_percent: float
):
    """
    Find the user defined trade from market_symbol and is_long in a dictionary positions and return
    a dictionary formatted correctly to close 100% of that trade

    Parameters
    ----------
    chain : str
        arbitrum or avalanche.
    positions : dict
        dictionary containing all open positions.
    market_symbol : str
        symbol of market trader.
    is_long : bool
        True for long, False for short.
    slippage_percent : float
        slippage tolerance to close trade as a percentage.

    Raises
    ------
    Exception
        If we can't find the requested trade for the user.

    Returns
    -------
    dict
        order parameters formatted to close the position.

    """
    direction = "short"
    if is_long:
        direction = "long"

    position_dictionary_key = "{}_{}".format(market_symbol.upper(),
                                             direction)

    try:
        raw_position_data = positions[position_dictionary_key]
        gmx_tokens = get_tokens_address_dict(chain)

        collateral_address = find_dictionary_by_key_value(gmx_tokens,
                                                          "symbol",
                                                          raw_position_data['collateral_token'])
        gmx_tokens = get_tokens_address_dict(chain)
        index_address = find_dictionary_by_key_value(gmx_tokens,
                                                     "symbol",
                                                     raw_position_data['market_symbol'])

        size_delta = int(raw_position_data['position_size'] * (10**30))

        return {
            "chain": chain,
            "market_key": raw_position_data['market'],
            "collateral_address": collateral_address["address"],
            "index_token_address": index_address["address"],
            "is_long": raw_position_data['is_long'],
            "size_delta": size_delta,
            "initial_collateral_delta": raw_position_data['inital_collateral_amount'],
            "slippage_percent": slippage_percent,
            "swap_path": []
        }
    except KeyError:
        raise Exception("Couldn't find a {} {} for given user!".format(market_symbol, direction))


if __name__ == "__main__":

    chain = "arbitrum"

    positions = get_positions(
        chain=chain,
        address=None
    )

    market_symbol = "ETH"
    is_long = False

    order_params = transform_open_position_to_order_parameters(chain,
                                                               positions,
                                                               market_symbol,
                                                               is_long,
                                                               0.003)
