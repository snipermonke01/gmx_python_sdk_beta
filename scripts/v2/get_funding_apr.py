#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 14:14:10 2023

@author: snipermonke01
"""

import json
import os

from .get_oracle_prices import GetOraclePrices
from .get_open_interest import OpenInterest
from .get_markets import GetMarkets
from .gmx_utils import get_reader_contract, contract_map, get_funding_factor_per_period, base_dir, \
    execute_threading, save_json_file_to_datastore, make_timestamped_dataframe, \
    save_csv_to_datastore


class GetFundingFee:

    def __init__(self, chain: str, use_local_datastore: bool = False):

        self.reader_contract = None
        self.data_store_contract_address = None
        self.chain = chain
        self.use_local_datastore = use_local_datastore

    def get_funding_apr(self, to_json: bool = False, to_csv: bool = False):
        """
        Call to get the funding APR across all pools on a given chain defined in class init. Pass
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

        data = self._get_funding_apr_dict()

        if to_json:
            save_json_file_to_datastore(
                "{}_funding_apr.json".format(self.chain),
                data
            )
        if to_csv:
            long_dataframe = make_timestamped_dataframe(data['long'])
            short_dataframe = make_timestamped_dataframe(data['short'])
            save_csv_to_datastore(
                "{}_long_funding_apr.csv".format(self.chain),
                long_dataframe
            )
            save_csv_to_datastore(
                "{}_short_funding_apr.csv".format(self.chain),
                short_dataframe
            )
        else:
            return data

    def _get_funding_apr_dict(self):
        """
        Generate the dictionary of funding APR data

        Returns
        -------
        funding_apr : dict
            dictionary of funding data.

        """

        # If passing true will use local instance of open interest data
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
            open_interest = OpenInterest(chain=self.chain).call_open_interest(to_json=False)

        self.reader_contract = get_reader_contract(self.chain)
        self.data_store_contract_address = contract_map[self.chain]['datastore']['contract_address']

        markets = GetMarkets(chain=self.chain).get_available_markets()

        print("\nGMX v2 Funding Rates (% per hour)")

        # define skeleton of output dictionary
        funding_apr = {
            "long": {
            },
            "short": {
            }
        }

        # define empty lists to pass to zip iterater later on
        mapper = []
        output_list = []
        long_interest_usd_list = []
        short_interest_usd_list = []

        # loop markets
        for market_key in markets:

            symbol = markets[market_key]['market_symbol']

            index_token_address = markets[market_key]['index_token_address']

            # if index address is 0 address, it is a swap market
            if index_token_address == "0x0000000000000000000000000000000000000000":
                continue

            long_token_address = markets[market_key]['long_token_address']
            short_token_address = markets[market_key]['short_token_address']

            output = self._make_market_info_query(market_key,
                                                  index_token_address,
                                                  long_token_address,
                                                  short_token_address)

            mapper = mapper + [symbol]
            output_list = output_list + [output]
            long_interest_usd_list = long_interest_usd_list + \
                [open_interest['long'][symbol]*10**30]
            short_interest_usd_list = short_interest_usd_list + \
                [open_interest['short'][symbol]*10**30]

        # Multithreaded call on contract
        threaded_output = execute_threading(output_list)
        for output, long_interest_usd, short_interest_usd, symbol in zip(
                threaded_output, long_interest_usd_list, short_interest_usd_list, mapper
        ):

            print("\n{}".format(symbol))

            market_info_dict = {
                "market_token": output[0][0],
                "index_token": output[0][1],
                "long_token": output[0][2],
                "short_token": output[0][3],
                "long_borrow_fee": output[1],
                "short_borrow_fee": output[2],
                "is_long_pays_short": output[4][0],
                "funding_factor_per_second": output[4][1]}

            long_funding_fee = get_funding_factor_per_period(market_info_dict,
                                                             True,
                                                             3600,
                                                             long_interest_usd,
                                                             short_interest_usd)

            print("Long funding hrly rate {:.4f}%".format(long_funding_fee))

            short_funding_fee = get_funding_factor_per_period(market_info_dict,
                                                              False,
                                                              3600,
                                                              long_interest_usd,
                                                              short_interest_usd)

            print("Short funding hrly rate {:.4f}%".format(short_funding_fee))

            funding_apr['long'][symbol] = long_funding_fee
            funding_apr['short'][symbol] = short_funding_fee

        return funding_apr

    # TODO - could potentially just pass market here and call each of the variables within method
    def _make_market_info_query(self,
                                market_key: str,
                                index_token_address: str,
                                long_token_address: str,
                                short_token_address: str):
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
        oracle_prices_dict = GetOraclePrices(self.chain).get_recent_prices()

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

        return self.reader_contract.functions.getMarketInfo(self.data_store_contract_address,
                                                            prices,
                                                            market_key)


if __name__ == "__main__":

    GetFundingFee(chain='arbitrum').get_funding_apr(to_csv=False)
