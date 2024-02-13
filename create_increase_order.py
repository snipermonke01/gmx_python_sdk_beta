from scripts.v2.create_increase_order import IncreaseOrder
from scripts.v2.order_argument_parser import OrderArgumentParser


parameters = {
    "chain": 'arbitrum',

    # the market you want to trade on
    "index_token_symbol": "ETH",

    # token to use as collateral. Start token swaps into collateral token if different
    "collateral_token_symbol": "ETH",

    # the token to start with - WETH not supported yet
    "start_token_symbol": "ETH",

    # True for long, False for short
    "is_long": False,

    # Position size in in USD
    "size_delta_usd": 2.5,

    # if leverage is passed, will calculate number of tokens in start_token_symbol amount
    "leverage": 1,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(is_increase=True).process_parameters_dictionary(parameters)

order = IncreaseOrder(
    chain=order_parameters['chain'],
    market_key=order_parameters['market_key'],
    collateral_address=order_parameters['start_token_address'],
    index_token_address=order_parameters['index_token_address'],
    is_long=order_parameters['is_long'],
    size_delta=order_parameters['size_delta'],
    initial_collateral_delta_amount=order_parameters['initial_collateral_delta'],
    slippage_percent=order_parameters['slippage_percent'],
    swap_path=order_parameters['swap_path']
)
