#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 21:20:01 2023

@author: snipermonke01
"""

import os
import json
import time

import numpy as np

from numerize import numerize

from .get_markets import GetMarkets
from .gmx_utils import base_dir, execute_threading, save_json_file_to_datastore, \
    make_timestamped_dataframe, save_csv_to_datastore

from .get_oracle_prices import GetOraclePrices
from .get_open_interest import OpenInterest
from .keys import (
    get_datastore_contract, pool_amount_key, reserve_factor_key,
    open_interest_reserve_factor_key
)


class GetAvailableLiquidity:

    def __init__(self, chain: str, use_local_datastore: bool = False):

        self.chain = chain
        self.use_local_datastore = use_local_datastore

    def get_available_liquidity(self, to_json: bool = False, to_csv: bool = False):
        """
        Call to get the available liquidity across all pools on a given chain defined in class
        init. Pass either to_json or to_csv to save locally in datastore

        Parameters
        ----------
        to_json : bool, optional
            save output to json file. The default is False.
        to_csv : bool, optional
            save out to csv file. The default is False.

        Returns
        -------
        data : dict
            dictionary of data.

        """
        data = self._available_liquidity()

        if to_json:
            save_json_file_to_datastore(
                "{}_available_liquidity.json".format(self.chain),
                data
            )

        if to_csv:
            long_dataframe = make_timestamped_dataframe(data['long'])
            short_dataframe = make_timestamped_dataframe(data['short'])
            save_csv_to_datastore(
                "{}_long_available_liquidity.csv".format(self.chain),
                long_dataframe
            )
            save_csv_to_datastore(
                "{}_short_available_liquidity.csv".format(self.chain),
                short_dataframe
            )

        else:
            return data

    def _available_liquidity(self):
        """
        Generate the dictionary of available liquidity

        Returns
        -------
        funding_apr : dict
            dictionary of available liquidity

        """
        if self.use_local_datastore:
            open_interest = json.load(
                open(
                    os.path.join(
                        base_dir,
                        "data_store",
                        "{}_open_interest.json".format(self.chain)
                    )
                )
            )
        else:
            open_interest = OpenInterest(chain=self.chain).call_open_interest(
                to_json=False
            )

        markets = GetMarkets(chain=self.chain).get_available_markets()
        available_liquidity = {
            "long": {
            },
            "short": {
            }
        }

        print("\nGMX v2 Available Liquidity\n")

        reserved_long_list = []
        reserved_short_list = []
        token_price_list = []
        mapper = []
        long_pool_amount_list = []
        long_reserve_factor_list = []
        long_open_interest_reserve_factor_list = []
        short_pool_amount_list = []
        short_reserve_factor_list = []
        short_open_interest_reserve_factor_list = []
        long_precision_list = []
        short_precision_list = []

        for market_key in markets:

            # this will filter out swap markets
            market_symbol = markets[market_key]['market_symbol']
            if "SWAP" in market_symbol:
                continue

            # collate market symbol to map dictionary later
            mapper = mapper + [market_symbol]

            # calculate long pool metrics
            long_token_address = markets[market_key]['long_token_address']
            long_pool_amount, long_reserve_factor,\
                long_open_interest_reserve_factor = self.get_max_reserved_usd(
                    market_key,
                    long_token_address,
                    True
                )
            long_precision = 10**(30+markets[market_key]['long_token_metadata']['decimals'])

            # collate long side lists to iterate through
            reserved_long_list = reserved_long_list + [open_interest['long'][market_symbol]]
            long_pool_amount_list = long_pool_amount_list + [long_pool_amount]
            long_reserve_factor_list = long_reserve_factor_list + [long_reserve_factor]
            long_open_interest_reserve_factor_list = long_open_interest_reserve_factor_list + \
                [long_open_interest_reserve_factor]
            long_precision_list = long_precision_list + [long_precision]

            # calculate short pool metrics
            short_token_address = markets[market_key]['short_token_address']
            short_pool_amount, short_reserve_factor, \
                short_open_interest_reserve_factor = self.get_max_reserved_usd(
                    market_key,
                    short_token_address,
                    False
                )
            short_precision = 10**(
                30 + markets[market_key]['short_token_metadata']['decimals']
            )

            # collate short side lists to iterate through
            reserved_short_list = reserved_short_list + [open_interest['short'][market_symbol]]
            short_pool_amount_list = short_pool_amount_list + [short_pool_amount]
            short_reserve_factor_list = short_reserve_factor_list + [short_reserve_factor]
            short_open_interest_reserve_factor_list = short_open_interest_reserve_factor_list + \
                [short_open_interest_reserve_factor]
            short_precision_list = short_precision_list + [short_precision]

            # calculate token price
            prices = GetOraclePrices(chain=self.chain).get_recent_prices()
            oracle_precision = 10**(30-markets[market_key]['long_token_metadata']['decimals'])

            token_price = np.median([float(
                prices[long_token_address]['maxPriceFull'])/oracle_precision,
                float(prices[long_token_address]['minPriceFull'])/oracle_precision]
            )

            # collate token price to iterate through
            token_price_list = token_price_list + [token_price]

        # TODO - Series of sleeps to stop ratelimit on the RPC, should have retry
        long_pool_amount_output = execute_threading(long_pool_amount_list)
        time.sleep(0.2)

        short_pool_amount_output = execute_threading(short_pool_amount_list)
        time.sleep(0.2)

        long_reserve_factor_list_output = execute_threading(long_reserve_factor_list)
        time.sleep(0.2)

        short_reserve_factor_list_output = execute_threading(short_reserve_factor_list)
        time.sleep(0.2)

        long_open_interest_reserve_factor_list_output = execute_threading(
            long_open_interest_reserve_factor_list
        )
        time.sleep(0.2)

        short_open_interest_reserve_factor_list_output = execute_threading(
            short_open_interest_reserve_factor_list
        )

        for long_pool_amount, short_pool_amount, long_reserve_factor, short_reserve_factor, \
                long_open_interest_reserve_factor, short_open_interest_reserve_factor, \
                reserved_long, reserved_short, token_price, token_symbol, long_precision, \
                short_precision in zip(
                    long_pool_amount_output,
                    short_pool_amount_output,
                    long_reserve_factor_list_output,
                    short_reserve_factor_list_output,
                    long_open_interest_reserve_factor_list_output,
                    short_open_interest_reserve_factor_list_output,
                    reserved_long_list,
                    reserved_short_list,
                    token_price_list,
                    mapper,
                    long_precision_list,
                    short_precision_list
                ):

            print(token_symbol)

            # select the lesser of maximum value of pool reserves or open interest limit
            if long_open_interest_reserve_factor < long_reserve_factor:
                long_reserve_factor = long_open_interest_reserve_factor

            long_max_reserved_tokens = (long_pool_amount*long_reserve_factor)

            long_max_reserved_usd = (
                long_max_reserved_tokens / long_precision * token_price
            )

            long_liquidity = long_max_reserved_usd - float(reserved_long)

            print("Available Long Liquidity: ${}".format(
                numerize.numerize(long_liquidity)
            )
            )
            available_liquidity['long'][token_symbol] = long_liquidity

            # select the lesser of maximum value of pool reserves or open interest limit
            if short_open_interest_reserve_factor < short_reserve_factor:
                short_reserve_factor = short_open_interest_reserve_factor

            short_max_reserved_usd = (short_pool_amount*short_reserve_factor)

            short_liquidity = (
                short_max_reserved_usd / short_precision - float(
                    reserved_short
                )
            )
            print("Available Short Liquidity: ${}\n".format(
                numerize.numerize(short_liquidity)
            )
            )

            available_liquidity['short'][token_symbol] = short_liquidity

        return available_liquidity

    def get_max_reserved_usd(self, market: str, token: str, is_long: bool):
        """
        For a given market, long/short token and pool direction get the uncalled web3 functions to
        calculate pool size, pool reserve factor and open interest reserve factor

        Parameters
        ----------
        market : str
            contract address of GMX market.
        token : str
            contract address of long or short token.
        is_long : bool
            pass True for long pool or False for short.

        Returns
        -------
        pool_amount : web3.contract_obj
            uncalled web3 contract object for pool amount.
        reserve_factor : web3.contract_obj
            uncalled web3 contract object for pool reserve factor.
        open_interest_reserve_factor : web3.contract_obj
            uncalled web3 contract object for open interest reserve factor.

        """

        # get web3 datastore object
        datastore = get_datastore_contract(self.chain)

        # get hashed keys for datastore
        pool_amount_hash_data = pool_amount_key(
            market,
            token
        )
        reserve_factor_hash_data = reserve_factor_key(
            market,
            is_long
        )
        open_interest_reserve_factor_hash_data = open_interest_reserve_factor_key(
            market,
            is_long
        )

        pool_amount = datastore.functions.getUint(
            pool_amount_hash_data
        )
        reserve_factor = datastore.functions.getUint(
            reserve_factor_hash_data
        )
        open_interest_reserve_factor = datastore.functions.getUint(
            open_interest_reserve_factor_hash_data
        )

        return pool_amount, reserve_factor, open_interest_reserve_factor


if __name__ == "__main__":

    data = GetAvailableLiquidity(chain="arbitrum",
                                 use_local_datastore=False).get_available_liquidity(to_csv=False)
