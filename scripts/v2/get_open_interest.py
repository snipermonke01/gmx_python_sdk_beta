#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 23:54:59 2023

@author: snipermonke01
"""

import time
import web3

from numerize import numerize

from .gmx_utils import contract_map, get_reader_contract, execute_threading, \
    save_json_file_to_datastore, make_timestamped_dataframe, save_csv_to_datastore
from .get_oracle_prices import GetOraclePrices
from .get_markets import GetMarkets


class OpenInterest:

    def __init__(self, chain: str):

        self.chain = chain

    def call_open_interest(self, to_json: bool = False, to_csv: bool = False):
        """
        Call to get the open interest across all pools on a given chain defined in class init. Pass
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
        data = self._get_open_interest()

        if to_json:
            save_json_file_to_datastore(
                "{}_open_interest.json".format(self.chain),
                data
            )
        if to_csv:
            long_dataframe = make_timestamped_dataframe(data['long'])
            short_dataframe = make_timestamped_dataframe(data['short'])
            save_csv_to_datastore(
                "{}_long_open_interest.csv".format(self.chain),
                long_dataframe
            )
            save_csv_to_datastore(
                "{}_short_open_interest.csv".format(self.chain),
                short_dataframe
            )
        else:
            return data

    def _get_open_interest(self):
        """
        Generate the dictionary of open interest data

        Returns
        -------
        funding_apr : dict
            dictionary of open interest data.

        """

        reader_contract = get_reader_contract(self.chain)
        data_store_contract_address = contract_map[self.chain]['datastore']['contract_address']
        markets = GetMarkets(chain=self.chain).get_available_markets()
        oracle_prices_dict = GetOraclePrices(chain=self.chain).get_recent_prices()
        print("GMX v2 Open Interest\n")
        open_interest = {
            "long": {
            },
            "short": {
            }
        }

        long_oi_output_list = []
        short_oi_output_list = []
        long_pnl_output_list = []
        short_pnl_output_list = []
        mapper = []
        long_precision_list = []

        for market_key in markets:

            # Skip swap markets
            if "SWAP" in markets[market_key]['market_symbol']:
                continue

            market = [market_key,
                      markets[market_key]['index_token_address'],
                      markets[market_key]['long_token_address'],
                      markets[market_key]['short_token_address']]
            prices_list = [
                int(oracle_prices_dict[markets[market_key]
                    ['index_token_address']]['minPriceFull']),
                int(oracle_prices_dict[markets[market_key]
                    ['index_token_address']]['maxPriceFull'])
            ]

            decimal_factor = markets[market_key]['long_token_metadata']['decimals']

            # If the market is a synthetic one we need to use the decimals from the index token
            try:
                if markets[market_key]['market_metadata']['synthetic']:
                    decimal_factor = markets[market_key]['market_metadata']['decimals']
            except KeyError:
                pass

            oracle_factor = 30-markets[market_key]['market_metadata']['decimals']

            precision = 10**(decimal_factor + oracle_factor)
            long_precision_list = long_precision_list + [precision]

            long_oi_with_pnl, long_pnl = self.make_query(reader_contract,
                                                         data_store_contract_address,
                                                         market,
                                                         prices_list,
                                                         is_long=True)

            short_oi_with_pnl, short_pnl = self.make_query(reader_contract,
                                                           data_store_contract_address,
                                                           market,
                                                           prices_list,
                                                           is_long=False)

            long_oi_output_list = long_oi_output_list + [long_oi_with_pnl]
            short_oi_output_list = short_oi_output_list + [short_oi_with_pnl]
            long_pnl_output_list = long_pnl_output_list + [long_pnl]
            short_pnl_output_list = short_pnl_output_list + [short_pnl]
            mapper = mapper + [markets[market_key]['market_symbol']]

        # TODO - currently just waiting x amount of time to not hit rate limit, but needs a retry
        long_oi_threaded_output = execute_threading(long_oi_output_list)
        time.sleep(0.2)
        short_oi_threaded_output = execute_threading(short_oi_output_list)
        time.sleep(0.2)
        long_pnl_threaded_output = execute_threading(long_pnl_output_list)
        time.sleep(0.2)
        short_pnl_threaded_output = execute_threading(short_pnl_output_list)

        for market_symbol, long_oi, short_oi, long_pnl, short_pnl, long_precision in zip(
            mapper,
            long_oi_threaded_output,
            short_oi_threaded_output,
            long_pnl_threaded_output,
            short_pnl_threaded_output,
            long_precision_list
        ):

            print("{} Long: ${}".format(market_symbol,
                                        numerize.numerize((long_oi-long_pnl)/long_precision)))

            open_interest['long'][market_symbol] = (long_oi-long_pnl)/long_precision

            precision = 10**30

            print("{} Short: ${}".format(market_symbol,
                                         numerize.numerize(((short_oi-short_pnl)/precision))))
            open_interest['short'][market_symbol] = (short_oi-short_pnl)/precision

        return open_interest

    def make_query(self,
                   reader_contract,
                   data_store_contract_address: str,
                   market: str,
                   prices_list: list,
                   is_long: bool,
                   maximize: bool = False):
        """
        Make query to reader contract to get open interest with pnl and the pnl for a given market
        and direction (set with is_long)

        Parameters
        ----------
        reader_contract : web3._utils.datatypes.Contract
            web3 object of the reader contract.
        data_store_contract_address : str
            address of the datastore contract.
        market : str
            address of the GMX market.
        prices_list : list
            list of min/max short, long, and index fast prices.
        is_long : bool
            is long or short.
        maximize : bool, optional
            either use min or max price. The default is False.

        Returns
        -------
        oi_with_pnl
            uncalled web3 query.
        pnl
            uncalled web3 query.

        """

        oi_with_pnl = reader_contract.functions.getOpenInterestWithPnl(data_store_contract_address,
                                                                       market,
                                                                       prices_list,
                                                                       is_long,
                                                                       maximize)
        pnl = reader_contract.functions.getPnl(data_store_contract_address,
                                               market,
                                               prices_list,
                                               is_long,
                                               maximize)

        return oi_with_pnl, pnl


if __name__ == '__main__':

    data = OpenInterest(chain="arbitrum").call_open_interest(to_csv=False)
