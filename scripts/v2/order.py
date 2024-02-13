import logging
import numpy as np

from hexbytes import HexBytes
from web3 import Web3

from .get_markets import GetMarkets
from .get_oracle_prices import GetOraclePrices
from .gmx_utils import (
    get_exchange_router_contract, create_connection, get_config, contract_map,
    PRECISION, get_execution_price_and_price_impact, order_type as order_types,
    decrease_position_swap_type as decrease_position_swap_types, determine_swap_route
)
from .gas_utils import get_execution_fee
from .approve_token_for_spend import check_if_approved


class Order:
    def __init__(
        self, chain: str, market_key: str, collateral_address: str,
        index_token_address: str, is_long: bool, size_delta: float,
        initial_collateral_delta_amount: str, slippage_percent: float,
        swap_path: list
    ) -> None:
        self.chain = chain
        self.market_key = market_key
        self.collateral_address = collateral_address
        self.index_token_address = index_token_address
        self.is_long = is_long
        self.size_delta = size_delta
        self.initial_collateral_delta_amount = initial_collateral_delta_amount
        self.slippage_percent = slippage_percent
        self.swap_path = swap_path

        self._exchange_router_contract_obj = get_exchange_router_contract(
            chain=self.chain
        )
        self._connection = create_connection(chain=self.chain)
        self._is_swap = False

        self.log = logging.getLogger(__name__)
        self.log.info("Creating order...")

    def determine_gas_limits(self):
        pass

    def check_for_approval(self):
        """
        Check for Approval

        NOTE: Doesn't function at the moment. Original code was excluded.
        """
        spender = contract_map[self.chain]["syntheticsrouter"]['contract_address']

        check_if_approved(self.chain,
                          spender,
                          self.collateral_address,
                          self.initial_collateral_delta_amount,
                          approve=True)

    def _submit_transaction(
        self, user_wallet_address: str, value_amount: float,
        multicall_args: list, gas_limits: dict
    ):
        """
        Submit Transaction
        """
        self.log.info("Submitting transaction...")

        nonce = self._connection.eth.get_transaction_count(
            Web3.to_checksum_address(user_wallet_address)
        )

        raw_txn = self._exchange_router_contract_obj.functions.multicall(
            multicall_args
        ).build_transaction(
            {
                'value': value_amount,
                'chainId': 42161,
                # TODO - this is NOT correct
                'gas': (
                    self._gas_limits_order_type.call() +
                    self._gas_limits_order_type.call()
                ),
                'maxFeePerGas': Web3.to_wei('0.1', 'gwei'),
                'maxPriorityFeePerGas': Web3.to_wei('0.1', 'gwei'),
                'nonce': nonce
            }
        )

        signed_txn = self._connection.eth.account.sign_transaction(
            raw_txn, get_config()['private_key']
        )
        tx_hash = self._connection.eth.send_raw_transaction(
            signed_txn.rawTransaction
        )
        self.log.info("Txn submitted!")
        self.log.info(
            "Check status: https://arbiscan.io/tx/{}".format(tx_hash.hex())
        )

        self.log.info("Transaction submitted!")

    def _get_prices(
        self, decimals: float, prices: float, is_open: bool = False,
        is_close: bool = False, is_swap: bool = False
    ):
        """
        Get Prices
        """
        self.log.info("Getting prices...")
        price = np.median(
            [
                float(prices[self.index_token_address]['maxPriceFull']),
                float(prices[self.index_token_address]['minPriceFull'])
            ]
        )
        if is_open:
            if self.is_long:
                slippage = str(
                    int(float(price) + float(price) * self.slippage_percent)
                )
            else:
                slippage = str(
                    int(float(price) - float(price) * self.slippage_percent)
                )
        elif is_close:
            if self.is_long:
                slippage = str(
                    int(float(price) - float(price) * self.slippage_percent)
                )
            else:
                slippage = str(
                    int(float(price) + float(price) * self.slippage_percent)
                )
        else:
            slippage = 0

        acceptable_price = 0
        if not is_swap:
            acceptable_price = int(slippage.ljust(16, '0'))

        acceptable_price_in_usd = (
            acceptable_price / 10 ** (PRECISION - decimals + 3)
        )

        self.log.info("Price: {}".format(price))
        self.log.info("Acceptable price: {}".format(acceptable_price))
        self.log.info(
            "Acceptable price in USD: {}".format(acceptable_price_in_usd)
        )

        return price, int(slippage), acceptable_price_in_usd

    def order_builder(self, is_open=False, is_close=False, is_swap=False):
        """
        Create Order
        """
        config = get_config()
        self.determine_gas_limits()
        gas_price = self._connection.eth.gas_price
        execution_fee = int(
            get_execution_fee(
                self._gas_limits,
                self._gas_limits_order_type,
                gas_price
            )
        )
        if not is_close:
            self.check_for_approval()
        if is_swap:
            execution_fee = int(execution_fee*1.5)
        else:
            execution_fee = int(execution_fee*1.2)

        markets = GetMarkets(chain=self.chain).get_available_markets()

        if is_swap:

            # we need to determine what market(s) our swap needs to route through based on in and out token
            swap_route, requires_multi_swap = determine_swap_route(
                markets,
                self.start_token,
                self.out_token
            )
        else:
            swap_route = self.swap_path

        initial_collateral_delta_amount = self.initial_collateral_delta_amount

        prices = GetOraclePrices(chain=self.chain).get_recent_prices()

        size_delta_price_price_impact = self.size_delta
        if is_close:
            size_delta_price_price_impact = size_delta_price_price_impact * -1

        execution_price_parameters = {
            'data_store_address': (
                contract_map[self.chain]["datastore"]['contract_address']
            ),
            'market_key': self.market_key,
            'index_token_price': [
                int(prices[self.index_token_address]['maxPriceFull']),
                int(prices[self.index_token_address]['minPriceFull'])
            ],
            'position_size_in_usd': 0,
            'position_size_in_tokens': 0,
            'size_delta': size_delta_price_price_impact,
            'is_long': self.is_long
        }

        decimals = markets[self.market_key]['market_metadata']['decimals']
        callback_gas_limit = 0
        min_output_amount = 0

        if is_open:
            order_type = order_types['market_increase']
        elif is_close:
            order_type = order_types['market_decrease']
        elif is_swap:
            order_type = order_types['market_swap']
            # Estimate amount of token out using a reader function, necessary
            # for multi swap
            estimated_output = self.estimated_swap_output(
                markets[swap_route[0]],
                self.collateral_address,
                initial_collateral_delta_amount
            )

            # this var will help to calculate the cost gas depending on the
            # operation
            self._get_limits_order_type = self._gas_limits['single_swap']
            if requires_multi_swap:
                estimated_output = self.estimated_swap_output(
                    markets[swap_route[1]],
                    "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                    int(
                        estimated_output["out_token_amount"] -
                        estimated_output["out_token_amount"] * self.slippage_percent
                    )
                )
                self._get_limits_order_type = self._gas_limits['swap_order']

            min_output_amount = estimated_output["out_token_amount"] - \
                estimated_output["out_token_amount"] * self.slippage_percent

        decrease_position_swap_type = decrease_position_swap_types['no_swap']

        should_unwrap_native_token = True
        referral_code = HexBytes(
            "0x0000000000000000000000000000000000000000000000000000000000000000"
        )
        user_wallet_address = config['user_wallet_address']
        eth_zero_address = "0x0000000000000000000000000000000000000000"
        ui_ref_address = "0x0000000000000000000000000000000000000000"
        gmx_market_address = Web3.to_checksum_address(self.market_key)

        price, acceptable_price, acceptable_price_in_usd = self._get_prices(
            decimals,
            prices,
            is_open,
            is_close,
            is_swap
        )
        mark_price = int(price)

        if is_close:
            mark_price = 0

        elif is_swap:
            mark_price = 0
            acceptable_price = 0
            gmx_market_address = "0x0000000000000000000000000000000000000000"

        execution_price_and_price_impact_dict = get_execution_price_and_price_impact(
            self.chain,
            execution_price_parameters,
            decimals
        )

        arguments = (
            (
                Web3.to_checksum_address(user_wallet_address),
                Web3.to_checksum_address(eth_zero_address),
                Web3.to_checksum_address(ui_ref_address),
                gmx_market_address,
                Web3.to_checksum_address(self.collateral_address),
                swap_route
            ),
            (
                self.size_delta,
                self.initial_collateral_delta_amount,
                mark_price,
                acceptable_price,
                execution_fee,
                callback_gas_limit,
                int(min_output_amount)
            ),
            order_type,
            decrease_position_swap_type,
            self.is_long,
            should_unwrap_native_token,
            referral_code
        )

        # If the collateral is not native token (ie ETH/Arbitrum or AVAX/AVAX)
        # need to send tokens to vault
        print(self.collateral_address)
        value_amount = execution_fee
        if (self.collateral_address !=
                '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1' and not is_close and not is_swap):

            multicall_args = [
                HexBytes(self._send_wnt(value_amount)),
                HexBytes(
                    self._send_tokens(
                        self.collateral_address,
                        initial_collateral_delta_amount
                    )
                ),
                HexBytes(self._create_order(arguments))
            ]

        else:
            # NOTE is this only for these two? Checking source code
            # and seems to exist for all by is_close
            if is_open or is_swap:

                value_amount = initial_collateral_delta_amount + execution_fee

            multicall_args = [
                HexBytes(self._send_wnt(value_amount)),
                HexBytes(self._create_order(arguments))
            ]

        self._submit_transaction(
            user_wallet_address, value_amount, multicall_args, self._gas_limits
        )

    def _create_order(self, arguments):
        """
        Create Order
        """
        return self._exchange_router_contract_obj.encodeABI(
            fn_name="createOrder",
            args=[arguments],
        )

    def _send_tokens(self, arguments, amount):
        """
        Send tokens
        """
        return self._exchange_router_contract_obj.encodeABI(
            fn_name="sendTokens",
            args=(
                self.collateral_address,
                '0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5',
                amount
            ),
        )

    def _send_wnt(self, amount):
        """
        Send WNT
        """
        return self._exchange_router_contract_obj.encodeABI(
            fn_name='sendWnt',
            args=(
                "0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5",
                amount
            )
        )
