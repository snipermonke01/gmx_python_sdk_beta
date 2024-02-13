from scripts.v2.create_decrease_order import DecreaseOrder
from scripts.v2.order_argument_parser import OrderArgumentParser


# Example of passing arguments through the Order parser to close the desired position
parameters = {
    "chain": 'arbitrum',

    "index_token_symbol": "ARB",

    "collateral_token_symbol": "USDC",

    # set start token the same as your collateral
    "start_token_symbol": "USDC",

    "is_long": False,

    # amount of your position you want to close in USD
    "size_delta_usd": 12,

    # amount of tokens NOT USD you want to remove as collateral.
    "initial_collateral_delta": 6,

    # as a percentage
    "slippage_percent": 0.03
}

order_parameters = OrderArgumentParser(is_decrease=True).process_parameters_dictionary(parameters)


order = DecreaseOrder(
    chain=order_parameters['chain'],
    market_key=order_parameters['market_key'],
    collateral_address=order_parameters['collateral_address'],
    index_token_address=order_parameters['index_token_address'],
    is_long=order_parameters['is_long'],
    size_delta=order_parameters['size_delta'],
    initial_collateral_delta_amount=order_parameters['initial_collateral_delta'],
    slippage_percent=order_parameters['slippage_percent'],
    swap_path=[]
)
