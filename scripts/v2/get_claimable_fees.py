#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 21:20:01 2023

@author: snipermonke01
"""

import os
import json

import numpy as np

from numerize import numerize

from .get_markets import GetMarkets
from .gmx_utils import base_dir, execute_threading, make_timestamped_dataframe, \
    save_csv_to_datastore, save_json_file_to_datastore
from .get_oracle_prices import GetOraclePrices

from .keys import get_datastore_contract, claimable_fee_amount_key


class GetClaimableFees:

    def __init__(self, chain: str):

        self.chain = chain

    def get_claimable_fees(self, to_json: bool = False, to_csv: bool = False):
        """
        Call to get the claimable fees across all pools on a given chain defined in class init. Pass
        either to_json or to_csv to save locally in datastore

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

        data = self._claimable_fees()

        if to_json:
            self.save_json_file_to_datastore(
                "{}_claimable_fees.json".format(self.chain),
                data
            )
        if to_csv:
            dataframe = make_timestamped_dataframe(data)
            save_csv_to_datastore(
                "{}_total_fees.csv".format(self.chain),
                dataframe
            )
        else:
            return data

    def _claimable_fees(self):
        """
        Get total fees dictionary

        Returns
        -------
        funding_apr : dict
            dictionary of total fees for week so far.

        """
        markets = GetMarkets(chain=self.chain).get_available_markets()

        total_fees = 0

        long_output_list = []
        short_output_list = []
        long_precision_list = []
        long_token_price_list = []
        mapper = []

        for market_key in markets:

            # TODO - currently filtering out swap markets
            market_symbol = markets[market_key]['market_symbol']
            if "SWAP" in market_symbol:
                continue

            long_token_address = markets[market_key]['long_token_address']
            short_token_address = markets[market_key]['short_token_address']

            # uncalled web3 object for long fees
            long_output = self._get_claimable_fee_amount(
                market_key,
                long_token_address
            )

            prices = GetOraclePrices(chain=self.chain).get_recent_prices()
            oracle_precision = 10**(30-markets[market_key]['long_token_metadata']['decimals'])
            long_token_price = np.median([float(
                prices[long_token_address]['maxPriceFull'])/oracle_precision,
                float(prices[long_token_address]['minPriceFull'])/oracle_precision]
            )

            long_token_price_list = long_token_price_list + [long_token_price]

            long_precision = 10**(
                markets[market_key]['long_token_metadata']['decimals']-1
            )

            long_precision_list = long_precision_list + [long_precision]

            # uncalled web3 object for short fees
            short_output = self._get_claimable_fee_amount(
                market_key,
                short_token_address
            )

            # add the uncalled web3 object to list
            long_output_list = long_output_list + [long_output]

            # add the uncalled web3 object to list
            short_output_list = short_output_list + [short_output]

            # add the market symbol to a list to use to map to dictionary later
            mapper = mapper + [markets[market_key]['market_symbol']]

        # feed the uncalled web3 objects into threading function
        long_threaded_output = execute_threading(long_output_list)
        short_threaded_output = execute_threading(short_output_list)

        for long_claimable_fees, short_claimable_fees, long_precision,\
                long_token_price, token_symbol, in zip(
                    long_threaded_output,
                    short_threaded_output,
                    long_precision_list,
                    long_token_price_list,
                    mapper
                ):

            # convert raw outputs into USD value
            long_claimable_usd = (
                long_claimable_fees/long_precision
            ) * long_token_price

            # TODO - currently all short fees are collected in USDC which is 6 decimals
            short_claimable_usd = short_claimable_fees/(10**6)

            print(token_symbol)
            print(
                "Long Claimable Fees: ${}".format(
                    numerize.numerize(long_claimable_usd)
                )
            )

            print("Short Claimable Fees: ${}\n".format(
                numerize.numerize(short_claimable_usd))
            )

            total_fees += long_claimable_usd + short_claimable_usd

        return {'latest_total_fees': total_fees}

    def _get_claimable_fee_amount(self, market_address: str, token_address: str):
        """
        For a given market and long/short side of the pool get the raw output for pending fees

        Parameters
        ----------
        market_address : str
            addess of the GMX market.
        token_address : str
            address of either long or short collateral token.

        Returns
        -------
        claimable_fee : web3 datastore obj
            uncalled obj of the datastore contract.

        """

        datastore = get_datastore_contract(self.chain)

        # create hashed key to query the datastore
        claimable_fees_amount_hash_data = claimable_fee_amount_key(
            market_address,
            token_address
        )

        claimable_fee = datastore.functions.getUint(
            claimable_fees_amount_hash_data
        )

        return claimable_fee


if __name__ == "__main__":

    data = GetClaimableFees(chain="arbitrum").get_claimable_fees(to_csv=True)
