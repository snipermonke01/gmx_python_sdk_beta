
# GMX Python SDK

A python based SDK developed for interacting with GMX v2

- [Requirements](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#requirements)
- [Config File Setup](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#config-file-setup)
- [Example Scripts](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#example-scripts)
- [General Usage](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#general-usage)
    - [Increase Position](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#increase-position)
    - [Decrease Position](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#decrease-position)
    - [Estimate Swap Output](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#estimate-swap-output)
    - [Helper Scripts](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#helper-scripts)
        - [Order Argument Parser](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#order-argument-parser)
        - [Closing Positions](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#closing-positions)
    - [GMX Stats](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#gmx-stats)
- [Known Limitations](https://github.com/snipermonke01/gmx_sdk/tree/main?tab=readme-ov-file#known-limitations)


## Requirements

Developed using:
```python
  python=3.10.4
```

Having issues installing using conda environment file, so try creating a new environment step by step with the following instructions:
```
conda create --name gmx_sdk python=3.10
conda activate gmx_sdk
pip install numpy
pip install hexbytes
pip install web3==6.10.0
pip install pyaml
pip install pandas==1.4.2
pip install numerize
```

The codebase is designed around the usage of web3py [6.10.0](https://web3py.readthedocs.io/en/stable/releases.html#web3-py-v6-10-0-2023-09-21), and will not work with older versions and has not been tested with the latest version.
## Config File Setup

[Config file](https://github.com/snipermonke01/gmx_sdk/blob/main/config.yaml) must set up before usage. For stats based operations, you will need only an RPC but for execution you need to save both a wallet address and the private key of that wallet. 

```yaml
arbitrum:
  rpc: rpc_url
  chain_id: chain_id
avalanche:
  rpc: rpc_url
  chain_id: chain_id
private_key: private_key
user_wallet_address: wallet_address
```

The example script [setting_config.py](https://github.com/snipermonke01/gmx_sdk/blob/main/setting_config.py) can be viewed for demonstration on how to import config and update with new details from script.

## Example Scripts

There are currently 4 example scripts which can be run:

- [identify_farming_opportunities.py](https://github.com/snipermonke01/gmx_sdk/blob/main/identify_farming_opportunities.py)
- [get_gmx_stats.py](https://github.com/snipermonke01/gmx_sdk/blob/main/get_gmx_stats.py)
- [create_increase_order.py](https://github.com/snipermonke01/gmx_sdk/blob/main/create_increase_order.py)
- [create_decrease_order.py](https://github.com/snipermonke01/gmx_sdk/blob/main/create_decrease_order.py)


## General Usage

### [Increase Position](https://github.com/snipermonke01/gmx_sdk/blob/main/create_increase_order.py)

The following block demonstrates how to open (or increase) a position:

```python
from scripts.v2.create_increase_order import IncreaseOrder

order = IncreaseOrder(
    chain,
    market_key,
    collateral_address,
    index_token_address,
    is_long,
    size_delta_usd,
    initial_collateral_delta_amount,
    slippage_percent,
    swap_path
)
```
**chain** - *type str*: either 'arbitrum' or 'avalanche' (avalanche currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to increase a position on

**collateral_address** - *type str*: the contract address of the token you want to use as collateral

**index_token_address** - *type str*: the contract address of the token you want to trade

**is_long** - *type bool*: True for long or False for short

**size_delta_usd** - *type int*: the size of position you want to open 10^30

**initial_collateral_delta_amount** - *type int*: the amount of token you want to use as collateral, 10^decimal of that token

**slippage_percent** - *type float*: the percentage you want to allow slippage

**swap_path** - *type list(str)*: a list of the GMX markets you will need to swap through if the starting token is different to the token you want to use as collateral

### [Decrease Position](https://github.com/snipermonke01/gmx_sdk/blob/main/create_decrease_order.py)

The following block demonstrates how to close (or decrease) a position:

```python
from scripts.v2.create_decrease_order import DecreaseOrder

order = DecreaseOrder(
    chain,
    market_key,
    collateral_address,
    index_token_address,
    is_long,
    size_delta_usd,
    initial_collateral_delta_amount,
    slippage_percent,
    swap_path
)
```
**chain** - *type str*: either 'arbitrum' or 'avalanche' (currently in testing still)

**market_key** - *type str*: the contract address of the GMX market you want to decrease a position for

**collateral_address** - *type str*: the contract address of the token you are using as collateral

**index_token_address** - *type str*: the contract address of the token are trading

**is_long** - *type bool*: True for long or False for short

**size_delta_usd** - *type int*: the size of the decrease to apply to your position, 10^30

**initial_collateral_delta_amount** - *type int*: the amount of collateral token you want to remove, 10^decimal of that token

**slippage_percent** - *type float*: the percentage you want to allow slippage

**swap_path** - *type list()*: empty list

### Get Execution Price & Price Impact On Position Change


```python
from scripts.v2.gmx_utils import get_execution_price_and_price_impact

chain = "arbitrum"
estimated_swap_output_parameters = {
    'data_store_address': (data_store_address),
    'market_addresses': [
        gmx_market_address,
        index_token_address,
        long_token_address,
        short_token_address
    ],
    'token_prices_tuple': [
        [
            int(max_price_of_index_token),
            int(min_price_of_index_token)
        ],
        [
            int(max_price_of_long_token),
            int(min_price_of_long_token)
        ],
        [
            int(max_price_of_short_token),
            int(min_price_of_short_token])
        ],
    ],
    'token_in': in_token_address,
    'token_amount_in': in_token_amount,
    'ui_fee_receiver': "0x0000000000000000000000000000000000000000"
}

get_execution_price_and_price_impact(
    chain,
    estimated_swap_output_parameters,
    decimals
)

```

### Estimate Swap output

Below shows an example of how to call the function get_estimated_swap_output. It most complex operation is building the value for the token_prices_token key. It requires the max/min prices as output by the gmx signed prices api. This will return a dictionary containing the amount of tokens output and the price impact in USD.

```python
from scripts.v2.gmx_utils import get_estimated_swap_output

chain = "arbitrum"
estimated_swap_output_parameters = {
    'data_store_address': (data_store_address),
    'market_addresses': [
        gmx_market_address,
        index_token_address,
        long_token_address,
        short_token_address
    ],
    'token_prices_tuple': [
        [
            int(max_price_of_index_token),
            int(min_price_of_index_token)
        ],
        [
            int(max_price_of_long_token),
            int(min_price_of_long_token)
        ],
        [
            int(max_price_of_short_token),
            int(min_price_of_short_token])
        ],
    ],
    'token_in': in_token_address,
    'token_amount_in': in_token_amount,
    'ui_fee_receiver': "0x0000000000000000000000000000000000000000"
}

get_estimated_swap_output(
    chain,
    estimated_swap_output_parameters,
)

```

### Helper Scripts

To assist in argument formatting, there are a few helper functions:

#### [Order Argument Parser](https://github.com/snipermonke01/gmx_sdk/blob/main/scripts/v2/order_argument_parser.py)

Human readable numbers can be parsed in a dictionary with the following keys/values which are processed by a class, OrderArgumentParser. This class should initialised with a bool to indicate is_increase, is_decrease, or is_swap, calling the method: "process_parameters_dictionary". This will output a dictionary containing the user input parameters reformatted to allow for successful order creation.

For increase:


```python
from scripts.v2.order_argument_parser import OrderArgumentParser


parameters = {
    "chain": 'arbitrum',

    # the market you want to trade on
    "index_token_symbol": "ARB",

    # the token you want as collateral
    "collateral_token_symbol": "ARB",

    # the token to start with
    "start_token_symbol": "USDC",

    # True for long, False for short
    "is_long": False,

    # in USD
    "size_delta": 6.69,

    # if leverage is passed, will calculate number of tokens in start_token_symbol amount
    "leverage": 1,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(is_increase=True).process_parameters_dictionary(parameters)
```

For decrease:

```python
from scripts.v2.order_argument_parser import OrderArgumentParser

parameters = {
    "chain": 'arbitrum',
    "index_token_symbol": "ARB",

    "collateral_token_symbol": "USDC",

    # set start token the same as your collateral
    "start_token_symbol": "USDC",
    "is_long": False,

    # amount of your position you want to close in USD
    "size_delta": 12,

    # amount of collateral you want to remove in collateral tokens
    "initial_collateral_delta": 6,

    # as a percentage
    "slippage_percent": 0.03
}


order_parameters = OrderArgumentParser(is_decrease=True).process_parameters_dictionary(parameters)
```

#### Closing positions

Instead of passing the parameters to close a position, if you are aware of the market symbol and the direction of the trade you want to close you can pass these to [transform_open_position_to_order_parameters](https://github.com/snipermonke01/gmx_sdk/blob/main/get_positions.py#L46) after collecting all open positions using [get_positions](https://github.com/snipermonke01/gmx_sdk/blob/main/get_positions.py#L13). This will output a formatted dictionary which will close 100% of the defined position.

```python
from get_positions import get_positions, transform_open_position_to_order_parameters

chain = "arbitrum"
market_symbol = "ETH"
is_long = False
slippage_percent = 0.003

# gets all open positions as a dictionary, with the keys as each position eg ETH_short
positions = get_positions(chain)

order_parameters = transform_open_position_to_order_parameters(
    chain,
    positions,
    market_symbol,
    is_long,
    slippage_percent
)
```

### GMX Stats

A number of stats can be obtained using a wide range of scripts. The overview on how to call these can be found in [get_gmx_stats](https://github.com/snipermonke01/gmx_sdk/blob/main/get_gmx_stats.py). Each method returns a dictionary containing long/short information for a given chain. When initialising the class, pass to_json or to_csv as True to save the output to the [data store](https://github.com/snipermonke01/gmx_sdk/tree/main/data_store): 

```python
from get_gmx_stats import GetGMXv2Stats

to_json = False
to_csv = False
chain = "arbitrum"

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
```

### Known Limitations

- Avalanche chain not fully tested
- A high rate limit RPC is required to read multiple sets of stats successively
