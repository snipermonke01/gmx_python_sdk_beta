#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 22:08:08 2023

@author: snipermonke01
"""

import pandas as pd

from datetime import datetime

from .get_oracle_prices import GetOraclePrices
from .get_markets import GetMarkets
from .gmx_utils import get_reader_contract, contract_map, execute_threading, \
    save_json_file_to_datastore, save_csv_to_datastore, make_timestamped_dataframe


class GetBorrowAPR:

    def __init__(self, chain: str):

        self.reader_contract = None
        self.data_store_contract_address = None
        self.chain = chain

    def get_borrow_apr(self, to_json: bool = False, to_csv: bool = False):
        """
        Call to get the borrow APR across all pools on a given chain defined in class init. Pass
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

        data = self._borrow_apr()

        if to_json:
            save_json_file_to_datastore(
                "{}_borrow_apr.json".format(self.chain),
                data
            )

        if to_csv:
            long_dataframe = make_timestamped_dataframe(data['long'])
            short_dataframe = make_timestamped_dataframe(data['short'])
            save_csv_to_datastore(
                "{}_long_borrow_apr.csv".format(self.chain),
                long_dataframe
            )
            save_csv_to_datastore(
                "{}_short_borrow_apr.csv".format(self.chain),
                short_dataframe
            )
        else:
            return data

    def _borrow_apr(self):
        """
        Generate the dictionary of borrow APR data

        Returns
        -------
        funding_apr : dict
            dictionary of borrow data.

        """

        self.data_store_contract_address = contract_map[self.chain]['datastore']['contract_address']

        markets = GetMarkets(chain=self.chain).get_available_markets()

        output_list = []
        mapper = []
        for market_key in markets:

            index_token_address = markets[market_key]['index_token_address']
            if index_token_address == "0x0000000000000000000000000000000000000000":
                continue
            long_token_address = markets[market_key]['long_token_address']
            short_token_address = markets[market_key]['short_token_address']

            output = self._make_market_info_query(market_key,
                                                  index_token_address,
                                                  long_token_address,
                                                  short_token_address)

            # add the uncalled web3 object to list
            output_list = output_list + [output]

            # add the market symbol to a list to use to map to dictionary later
            mapper = mapper + [markets[market_key]['market_symbol']]

        # feed the uncalled web3 objects into threading function
        threaded_output = execute_threading(output_list)

        borrow_apr_dict = {
            "long": {
            },
            "short": {
            }
        }
        for key, output in zip(mapper, threaded_output):
            borrow_apr_dict["long"][key] = (output[1]/10**28)*3600
            borrow_apr_dict["short"][key] = (output[2]/10**28)*3600
            print(
                "{}\nLong Borrow Hourly Rate: -{:.5f}%\nShort Borrow Hourly Rate: -{:.5f}%\n".format(
                    key,
                    borrow_apr_dict["long"][key],
                    borrow_apr_dict["short"][key]
                )
            )
        return borrow_apr_dict

    # TODO - could potentially just pass market here and call each of the variables within method
    def _make_market_info_query(self,
                                market_key,
                                index_token_address,
                                long_token_address,
                                short_token_address):
        """
        For a given market get the marketInfo from the reader contract

        Parameters
        ----------
        market_key : str
            address of GMX market.
        index_token_address : str
            address of index token.
        long_token_address : str
            address of long collateral token.
        short_token_address : str
            address of short collateral token.

        Returns
        -------
        reader_contract object
            unexecuted reader contract object.

        """

        reader_contract = get_reader_contract(chain=self.chain)

        oracle_prices_dict = GetOraclePrices(chain=self.chain).get_recent_prices()
        try:
            prices = (
                (
                    int(oracle_prices_dict[index_token_address]['minPriceFull']),
                    int(oracle_prices_dict[index_token_address]['maxPriceFull'])
                ),
                (
                    int(oracle_prices_dict[long_token_address]['minPriceFull']),
                    int(oracle_prices_dict[long_token_address]['maxPriceFull'])
                ),
                (
                    int(oracle_prices_dict[short_token_address]['minPriceFull']),
                    int(oracle_prices_dict[short_token_address]['maxPriceFull'])
                ))

        # TODO - this needs to be here until GMX add stables to signed price API
        except KeyError:
            prices = (
                (
                    int(oracle_prices_dict[index_token_address]['minPriceFull']),
                    int(oracle_prices_dict[index_token_address]['maxPriceFull'])
                ),
                (
                    int(oracle_prices_dict[long_token_address]['minPriceFull']),
                    int(oracle_prices_dict[long_token_address]['maxPriceFull'])
                ),
                (
                    int(1000000000000000000000000),
                    int(1000000000000000000000000)
                ))

        return reader_contract.functions.getMarketInfo(self.data_store_contract_address,
                                                       prices,
                                                       market_key)


if __name__ == "__main__":

    data = GetBorrowAPR(chain='arbitrum').get_borrow_apr(to_csv=False)
