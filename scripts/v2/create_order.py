from create_increase_order import IncreaseOrder
from create_decrease_order import DecreaseOrder
from create_swap_order import SwapOrder


chain = 'arbitrum'

market_key = "0xC25cEf6061Cf5dE5eb761b50E4743c1F5D7E5407"

collateral_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"

index_token_address = '0x912CE59144191C1204E64559FE8253a0e49E6548'

is_long = True

size_delta = int(5*10**30)

initial_collateral_delta_amount = int(1*10**18)

slippage_percent = 0.005

out_token = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"


order = IncreaseOrder(
    chain=chain,
    market_key=market_key,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta=size_delta,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=[]

)

order = DecreaseOrder(
    chain=chain,
    market_key=market_key,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta_usd=size_delta,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=[]
)

order = SwapOrder(
    out_token=out_token,
    chain=chain,
    market_key=market_key,
    collateral_address=collateral_address,
    index_token_address=index_token_address,
    is_long=is_long,
    size_delta=size_delta,
    initial_collateral_delta_amount=initial_collateral_delta_amount,
    slippage_percent=slippage_percent,
    swap_path=[]
)
