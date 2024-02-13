from web3 import Web3

from .order import Order
from .gas_utils import get_gas_limits
from .get_oracle_prices import GetOraclePrices
from .gmx_utils import (
    find_dictionary_by_key_value, get_estimated_swap_output, contract_map,
    get_datastore_contract
)


class SwapOrder(Order):
    """
    Open a swap order
    Extends base Order class
    """

    def __init__(self, start_token: str, out_token: str, *args: list, **kwargs: dict) -> None:
        super().__init__(
            *args, **kwargs
        )
        self.start_token = start_token
        self.out_token = out_token
        # order_approved = self.check_for_approval()

        # Open an order
        self.order_builder(is_swap=True)

    def determine_gas_limits(self):
        datastore = get_datastore_contract(self.chain)
        self._gas_limits = get_gas_limits(datastore)
        self._gas_limits_order_type = self._gas_limits["swap_order"]

    def estimated_swap_output(self, market, in_token, in_token_amount):
        print(in_token)
        prices = GetOraclePrices(chain=self.chain).get_recent_prices()

        # For every path we through we need to call this to get the expected
        # output after x number of swaps
        estimated_swap_output_parameters = {
            'data_store_address': (
                contract_map[self.chain]["datastore"]['contract_address']
            ),
            'market_addresses': [
                market['gmx_market_address'],
                market['index_token_address'],
                market['long_token_address'],
                market['short_token_address']
            ],
            'token_prices_tuple': [
                [
                    int(prices[market['index_token_address']]['maxPriceFull']),
                    int(prices[market['index_token_address']]['minPriceFull'])
                ],
                [
                    int(prices[market['long_token_address']]['maxPriceFull']),
                    int(prices[market['long_token_address']]['minPriceFull'])
                ],
                [
                    int(prices[market['short_token_address']]['maxPriceFull']),
                    int(prices[market['short_token_address']]['minPriceFull'])
                ],
            ],
            'token_in': Web3.to_checksum_address(in_token),
            'token_amount_in': in_token_amount,
            'ui_fee_receiver': "0x0000000000000000000000000000000000000000"
        }

        decimals = market['market_metadata']['decimals']

        estimated_swap_output = get_estimated_swap_output(
            self.chain,
            estimated_swap_output_parameters,
            decimals
        )

        return estimated_swap_output
