#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 10:01:23 2023

@author: snipermonke01
"""

from .gmx_utils import (
    contract_map, get_tokens_address_dict, get_reader_contract
)


class GetMarkets:

    def __init__(self, chain):

        self.chain = chain

    def get_available_markets(self):
        """
        Get the available markets on a given chain

        Returns
        -------
        Markets: dict
            dictionary of the available markets.

        """

        return self._process_markets()

    def _get_available_markets_raw(self):
        """
        Get the available markets from the reader contract

        Returns
        -------
        Markets: tuple
            tuple of raw output from the reader contract.

        """

        reader_contract = get_reader_contract(self.chain)
        data_store_contract_address = contract_map[self.chain]['datastore']['contract_address']

        return reader_contract.functions.getMarkets(
            data_store_contract_address, 0, 15
        ).call()

    def _process_markets(self):
        """
        Call and process the raw market data 

        Returns
        -------
        decoded_markets : dict
            dictionary decoded market data.

        """
        token_address_dict = get_tokens_address_dict(self.chain)

        raw_markets = self._get_available_markets_raw()

        decoded_markets = {}

        for raw_market in raw_markets:
            try:
                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': token_address_dict[raw_market[1]]['symbol'],
                    'index_token_address': raw_market[1],
                    'market_metadata': token_address_dict[raw_market[1]],
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }

            # If KeyError it is because there is no market symbol and it is a swap market
            except KeyError:

                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    ),
                    'index_token_address': raw_market[1],
                    'market_metadata': {'symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    )},
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }

        return decoded_markets


if __name__ == '__main__':

    raw_markets = GetMarkets(chain="arbitrum").get_available_markets(clean=False)
