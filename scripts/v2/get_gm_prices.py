#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 21:57:52 2023

@author: snipermonke01
"""

from .gmx_utils import get_reader_contract, contract_map, execute_threading, \
    save_json_file_to_datastore, make_timestamped_dataframe, save_csv_to_datastore

from .get_oracle_prices import GetOraclePrices
from .get_markets import GetMarkets
from .keys import MAX_PNL_FACTOR_FOR_TRADERS, MAX_PNL_FACTOR_FOR_DEPOSITS, \
    MAX_PNL_FACTOR_FOR_WITHDRAWALS


class GMPrices:

    def __init__(self, chain: str):

        self.chain = chain
        self.to_json = None
        self.to_csv = None

    def get_price_withdraw(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GM price if withdrawing from LP

        Parameters
        ----------
        to_json : bool, optional
            pass True to save price to json. The default is False.
        to_csv : bool, optional
            pass True to save price to json. The default is False.

        Returns
        -------
        gm_pool_prices: dict
            dictionary of gm prices.

        """

        self.to_json = to_json
        self.to_csv = to_csv
        pnl_factor_type = MAX_PNL_FACTOR_FOR_WITHDRAWALS

        return self._get_prices(pnl_factor_type)

    def get_price_deposit(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GM price if depositing to LP

        Parameters
        ----------
        to_json : bool, optional
            pass True to save price to json. The default is False.
        to_csv : bool, optional
            pass True to save price to json. The default is False.

        Returns
        -------
        gm_pool_prices: dict
            dictionary of gm prices.

        """

        self.to_json = to_json
        self.to_csv = to_csv
        pnl_factor_type = MAX_PNL_FACTOR_FOR_DEPOSITS
        return self._get_prices(pnl_factor_type)

    def get_price_traders(self, to_json: bool = False, to_csv: bool = False):
        """
        Get GM price if trading from LP

        Parameters
        ----------
        to_json : bool, optional
            pass True to save price to json. The default is False.
        to_csv : bool, optional
            pass True to save price to json. The default is False.

        Returns
        -------
        gm_pool_prices: dict
            dictionary of gm prices.

        """

        self.to_json = to_json
        self.to_csv = to_csv
        pnl_factor_type = MAX_PNL_FACTOR_FOR_TRADERS
        return self._get_prices(pnl_factor_type)

    def _get_prices(self, pnl_factor_type):
        """
        Get GM pool prices for a given profit/loss factor

        Parameters
        ----------
        pnl_factor_type : hash
            descriptor for datastore.

        Returns
        -------
        gm_pool_prices : dict
            dictionary of gm prices.

        """

        markets = GetMarkets(chain=self.chain).get_available_markets()
        prices = GetOraclePrices(chain=self.chain).get_recent_prices()

        output_list = []
        mapper = []
        for market_key in markets:

            # TODO - Does not get swap market GM prices currently
            if "SWAP" in markets[market_key]['market_symbol']:
                continue

            market = [
                market_key,
                markets[market_key]['index_token_address'],
                markets[market_key]['long_token_address'],
                markets[market_key]['short_token_address']
            ]

            index_price_tuple = [
                int(prices[markets[market_key]['index_token_address']]['minPriceFull']),
                int(prices[markets[market_key]['index_token_address']]['maxPriceFull'])
            ]

            long_price_tuple = [
                int(prices[markets[market_key]['long_token_address']]['minPriceFull']),
                int(prices[markets[market_key]['long_token_address']]['maxPriceFull'])
            ]

            # TODO - needs to be here until GMX add stables to signed prices API
            try:
                short_price_tuple = [
                    int(prices[markets[market_key]['short_token_address']]['minPriceFull']),
                    int(prices[markets[market_key]['short_token_address']]['maxPriceFull'])
                ]
            except KeyError:
                short_price_tuple = [
                    int(1000000000000000000000000),
                    int(1000000000000000000000000)
                ]

            output = self._make_market_token_price_query(
                market,
                index_price_tuple,
                long_price_tuple,
                short_price_tuple,
                pnl_factor_type
            )

            # add the uncalled web3 object to list
            output_list = output_list + [output]

            # add the market symbol to a list to use to map to dictionary later
            mapper = mapper + [markets[market_key]['market_symbol']]

        # feed the uncalled web3 objects into threading function
        threaded_output = execute_threading(output_list)

        gm_pool_prices = {}
        for key, output in zip(mapper, threaded_output):

            # divide by 10**30 to turn into USD value
            gm_pool_prices[key] = output[0]/10**30

        if self.to_json:

            filename = "{}_gm_prices.json".format(self.chain)
            save_json_file_to_datastore(
                filename,
                gm_pool_prices
            )

        if self.to_csv:

            dataframe = make_timestamped_dataframe(gm_pool_prices)

            save_csv_to_datastore(
                "{}_gm_prices.csv".format(self.chain),
                dataframe)

        return gm_pool_prices

    def _make_market_token_price_query(
            self,
            market: list,
            index_price_tuple: tuple,
            long_price_tuple: tuple,
            short_price_tuple: tuple,
            pnl_factor_type
    ):
        """
        Get the raw GM price from the reader contract for a given market tuple, index, long, and
        short max/min price tuples, and the pnl factor hash.

        Parameters
        ----------
        market : list
            list containing contract addresses of the market.
        index_price_tuple : tuple
            tuple of min and max prices.
        long_price_tuple : tuple
            tuple of min and max prices..
        short_price_tuple : tuple
            tuple of min and max prices..
        pnl_factor_type : hash
            descriptor for datastore.

        Returns
        -------
        output : TYPE
            DESCRIPTION.

        """

        reader_contract = get_reader_contract(self.chain)
        data_store_contract_address = (
            contract_map[self.chain]['datastore']['contract_address']
        )

        # maximise to take max prices in calculation
        maximise = True
        output = reader_contract.functions.getMarketTokenPrice(
            data_store_contract_address,
            market,
            index_price_tuple,
            long_price_tuple,
            short_price_tuple,
            pnl_factor_type,
            maximise
        )

        return output


if __name__ == "__main__":

    output = GMPrices(chain="arbitrum").get_price_traders(to_csv=True)
