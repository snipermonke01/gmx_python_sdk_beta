#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 29 17:47:25 2023

@author: snipermonke
"""

from scripts.v2.get_available_liquidity import GetAvailableLiquidity
from scripts.v2.get_borrow_apr import GetBorrowAPR
from scripts.v2.get_claimable_fees import GetClaimableFees
from scripts.v2.get_contract_balance import GetPoolTVL as ContractTVL
from scripts.v2.get_funding_apr import GetFundingFee
from scripts.v2.get_gm_prices import GMPrices
from scripts.v2.get_markets import GetMarkets
from scripts.v2.get_open_interest import OpenInterest
from scripts.v2.get_oracle_prices import GetOraclePrices
from scripts.v2.get_pool_tvl import GetPoolTVL


class GetGMXv2Stats:

    def __init__(self, to_json, to_csv):

        self.to_json = to_json
        self.to_csv = to_csv

    def get_available_liquidity(self, chain):

        return GetAvailableLiquidity(
            chain=chain
        ).get_available_liquidity(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_borrow_apr(self, chain):

        return GetBorrowAPR(
            chain=chain
        ).get_borrow_apr(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_claimable_fees(self, chain):

        return GetClaimableFees(
            chain=chain
        ).get_claimable_fees(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_contract_tvl(self, chain):

        return ContractTVL(
            chain=chain
        ).get_pool_balances(
            to_json=self.to_json
        )

    def get_funding_apr(self, chain):

        return GetFundingFee(
            chain=chain
        ).get_funding_apr(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_gm_price(self, chain):

        return GMPrices(
            chain=chain
        ).get_price_traders(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_available_markets(self, chain):

        return GetMarkets(
            chain=chain
        ).get_available_markets()

    def get_open_interest(self, chain):

        return OpenInterest(
            chain=chain
        ).call_open_interest(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_oracle_prices(self, chain):

        return GetOraclePrices(
            chain=chain
        ).get_recent_prices()

    def get_pool_tvl(self, chain):

        return GetPoolTVL(
            chain=chain
        ).get_pool_balances(
            to_csv=self.to_csv,
            to_json=self.to_json
        )


if __name__ == "__main__":

    to_json = False
    to_csv = False
    chain = "avalanche"

    stats_object = GetGMXv2Stats(
        to_json=to_json,
        to_csv=to_csv
    )

    liquidity = stats_object.get_available_liquidity(chain=chain)
    borrow_apr = stats_object.get_borrow_apr(chain=chain)
    claimable_fees = stats_object.get_claimable_fees(chain=chain)
    contract_tvl = stats_object.get_contract_tvl(chain=chain)
    funding_apr = stats_object.get_funding_apr(chain=chain)
    gm_prices = stats_object.get_gm_price(chain=chain)
    markets = stats_object.get_available_markets(chain=chain)
    open_interest = stats_object.get_open_interest(chain=chain)
    oracle_prices = stats_object.get_oracle_prices(chain=chain)
    pool_tvl = stats_object.get_pool_tvl(chain=chain)
