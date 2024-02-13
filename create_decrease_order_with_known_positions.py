from scripts.v2.create_decrease_order import DecreaseOrder
from scripts.v2.order_argument_parser import OrderArgumentParser
from get_positions import get_positions, transform_open_position_to_order_parameters


close_by_user_input = False
close_using_onchain_data = True


# This is how we can take some inputs an pass them throught the OrderArgumentClass to clean
if close_by_user_input:

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


# This is an example using the get_positions script to find open positions and close using this
if close_using_onchain_data:

    chain = "arbitrum"
    market_symbol = "ETH"
    is_long = False
    slippage_percent = 0.003

    # gets all open positions as a dictionary, which the keys as each position
    positions = get_positions(chain)

    order_parameters = transform_open_position_to_order_parameters(chain,
                                                                   positions,
                                                                   market_symbol,
                                                                   is_long,
                                                                   slippage_percent)


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
