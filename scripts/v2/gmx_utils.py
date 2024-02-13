#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 09:48:13 2023

@author: snipermonke01
"""

from eth_abi import encode
from web3 import Web3
import yaml
import logging
import os
import json
import requests

import pandas as pd

from datetime import datetime

from concurrent.futures import ThreadPoolExecutor


base_dir = os.path.join(os.path.dirname(__file__), '..', '..')

logging.basicConfig(
    format='{asctime} {levelname}: {message}',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    style='{',
    level=logging.INFO
)


def execute_call(call):
    return call.call()


def execute_threading(function_calls):

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(execute_call, function_calls))
    return results


contract_map = {
    'arbitrum':
    {
        "datastore":
        {
            "contract_address": "0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8",
            "abi_path": "contracts/v2/arbitrum/datastore.json"
        },
        "eventemitter":
        {
            "contract_address": "0xC8ee91A54287DB53897056e12D9819156D3822Fb",
            "abi_path": "contracts/v2/arbitrum/eventemitter.json"
        },
        "exchangerouter":
        {
            "contract_address": "0x7C68C7866A64FA2160F78EEaE12217FFbf871fa8",
            "abi_path": "contracts/v2/arbitrum/exchangerouter.json"
        },
        "depositvault":
        {
            "contract_address": "0xF89e77e8Dc11691C9e8757e84aaFbCD8A67d7A55",
            "abi_path": "contracts/v2/arbitrum/depositvault.json"
        },
        "withdrawalvault":
        {
            "contract_address": "0x0628D46b5D145f183AdB6Ef1f2c97eD1C4701C55",
            "abi_path": "contracts/v2/arbitrum/withdrawalvault.json"
        },
        "ordervault":
        {
            "contract_address": "0x31eF83a530Fde1B38EE9A18093A333D8Bbbc40D5",
            "abi_path": "contracts/v2/arbitrum/ordervault.json"
        },
        "syntheticsreader":
        {
            "contract_address": "0xf60becbba223EEA9495Da3f606753867eC10d139",
            "abi_path": "contracts/v2/arbitrum/syntheticsreader.json"
        },
        "syntheticsrouter":
        {
            "contract_address": "0x7452c558d45f8afC8c83dAe62C3f8A5BE19c71f6",
            "abi_path": "contracts/v2/arbitrum/syntheticsrouter.json"
        }
    },
    'avalanche':
    {
        "datastore":
        {
            "contract_address": "0x2F0b22339414ADeD7D5F06f9D604c7fF5b2fe3f6",
            "abi_path": "contracts/v2/avalanche/datastore.json"
        },
        "eventemitter":
        {
            "contract_address": "0xDb17B211c34240B014ab6d61d4A31FA0C0e20c26",
            "abi_path": "contracts/v2/avalanche/eventemitter.json"
        },
        "exchangerouter":
        {
            "contract_address": "0x79be2F4eC8A4143BaF963206cF133f3710856D0a",
            "abi_path": "contracts/v2/avalanche/exchangerouter.json"
        },
        "depositvault":
        {
            "contract_address": "0x90c670825d0C62ede1c5ee9571d6d9a17A722DFF",
            "abi_path": "contracts/v2/avalanche/depositvault.json"
        },
        "withdrawalvault":
        {
            "contract_address": "0xf5F30B10141E1F63FC11eD772931A8294a591996",
            "abi_path": "contracts/v2/avalanche/withdrawalvault.json"
        },
        "ordervault":
        {
            "contract_address": "0xD3D60D22d415aD43b7e64b510D86A30f19B1B12C",
            "abi_path": "contracts/v2/avalanche/ordervault.json"
        },
        "syntheticsreader":
        {
            "contract_address": "0x1D5d64d691FBcD8C80A2FD6A9382dF0fe544cBd8",
            "abi_path": "contracts/v2/avalanche/syntheticsreader.json"
        },
        "syntheticsrouter":
        {
            "contract_address": "0x820F5FfC5b525cD4d88Cd91aCf2c28F16530Cc68",
            "abi_path": "contracts/v2/avalanche/syntheticsrouter.json"
        }
    }
}


def get_config():
    config = yaml.safe_load(open(os.path.join(base_dir, "config.yaml")))

    if config['private_key'] is None:
        logging.warning("Private key not set!")

    if config['arbitrum']['rpc'] is None:
        logging.warning("Arbitrum RPC not set!")

    if config['avalanche']['rpc'] is None:
        logging.warning("Avalanche RPC not set!")

    return config


def create_connection(rpc: str = None, chain: str = None):
    """
    Create a connection to the blockchain
    """
    if rpc is None:
        rpc = get_config()[chain]['rpc']

    web3_obj = Web3(Web3.HTTPProvider(rpc))

    return web3_obj


def convert_to_checksum_address(chain: str, address: str):

    web3_obj = create_connection(chain=chain)

    return web3_obj.toChecksumAddress(address)


def get_contract_object(web3_obj, contract_name: str, chain: str):
    """
    Get the contract object from the contract map
    """
    contract_address = contract_map[chain][contract_name]["contract_address"]

    contract_abi = json.load(
        open(
            os.path.join(
                base_dir,
                contract_map[chain][contract_name]["abi_path"]
            )
        )
    )
    return web3_obj.eth.contract(
        address=contract_address,
        abi=contract_abi
    )


def get_token_balance_contract(chain, contract_address):
    """
    Get the token balance contract object
    """
    rpc = get_config()[chain]['rpc']

    web3_obj = create_connection(rpc)
    contract_abi = json.load(
        open(
            os.path.join(
                base_dir,
                'contracts',
                'v2',
                'balance_abi.json'
            )
        )
    )
    return web3_obj.eth.contract(
        address=contract_address,
        abi=contract_abi
    )


def get_tokens_address_dict(chain):
    """
    Get the token address dictionary
    """

    url = {
        "arbitrum": "https://arbitrum-api.gmxinfra.io/tokens",
        "avalanche": "https://avalanche-api.gmxinfra.io/tokens"
    }

    try:
        response = requests.get(url[chain])

        # Check if the request was successful (status code 200)
        if response.status_code == 200:

            # Parse the JSON response
            token_infos = response.json()['tokens']
        else:
            print(f"Error: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {e}")

    token_address_dict = {}

    for token_info in token_infos:
        token_address_dict[token_info['address']] = token_info

    return token_address_dict


def get_reader_contract(chain):
    rpc = get_config()[chain]['rpc']

    web3_obj = create_connection(rpc)
    return get_contract_object(
        web3_obj,
        'syntheticsreader',
        chain
    )


def get_event_emitter_contract(chain):
    rpc = get_config()[chain]['rpc']

    web3_obj = create_connection(rpc)
    return get_contract_object(
        web3_obj,
        'eventemitter',
        chain
    )


def get_datastore_contract(chain):
    rpc = get_config()[chain]['rpc']

    web3_obj = create_connection(rpc)
    return get_contract_object(
        web3_obj,
        'datastore',
        chain
    )


def get_exchange_router_contract(chain):
    rpc = get_config()[chain]['rpc']

    web3_obj = create_connection(rpc)
    return get_contract_object(
        web3_obj,
        'exchangerouter',
        chain
    )


def create_signer(chain):
    config = get_config()

    private_key = config['private_key']
    rpc = config[chain]['rpc']
    web3_obj = create_connection(rpc)

    return web3_obj.eth.account.from_key(private_key)


def create_hash(data_type_list, data_value_list):
    byte_data = encode(data_type_list, data_value_list)
    return Web3.keccak(byte_data)


def create_hash_string(string):
    return create_hash(["string"], [string])


def funding_fee_from_consensus(oi_imbalance, initial_oi, position, consensus):
    funding_factor = 0.00000002
    funding_exponent_factor = 1

    funding_factor_per_second = funding_factor
    oi_imbalance = oi_imbalance + (position if consensus else -1*position)
    funding_exponent_factor = funding_exponent_factor
    total_OI = initial_oi + position

    funding_fee_per_second = (funding_factor_per_second*oi_imbalance **
                              funding_exponent_factor) / total_OI
    funding_fee_hour = funding_fee_per_second * 3600

    return funding_fee_hour


def funding_fee_to_contrarian(initial_oi, oi_imbalance, position, consensus):
    ffh = funding_fee_from_consensus(
        oi_imbalance,
        initial_oi,
        position,
        consensus
    )
    OI_dominant = (
        initial_oi + oi_imbalance
    ) / 2 + (position if consensus else 0)
    OI_nondominant = (
        initial_oi - oi_imbalance
    ) / 2 + (position if not consensus else 0)
    ffh_to_contrarian = ffh * (OI_dominant/OI_nondominant)

    return ffh_to_contrarian


def get_execution_price_and_price_impact(chain, params, decimals):

    reader_contract_obj = get_reader_contract(chain)

    output = reader_contract_obj.functions.getExecutionPrice(
        params['data_store_address'],
        params['market_key'],
        params['index_token_price'],
        params['position_size_in_usd'],
        params['position_size_in_tokens'],
        params['size_delta'],
        params['is_long'],
    ).call()

    return {'execution_price': output[2] / 10**(PRECISION-decimals),
            'price_impact_usd': output[0] / 10**PRECISION}


def get_estimated_swap_output(chain, params, decimals):

    reader_contract_obj = get_reader_contract(chain)

    output = reader_contract_obj.functions.getSwapAmountOut(
        params['data_store_address'],
        params['market_addresses'],
        params['token_prices_tuple'],
        params['token_in'],
        params['token_amount_in'],
        params['ui_fee_receiver'],
    ).call()
    print(output)
    return {'out_token_amount': output[0],
            'price_impact_usd': output[1]
            }


order_type = {
    "market_swap": 0,
    "limit_swap": 1,
    "market_increase": 2,
    "limit_increase": 3,
    "market_decrease": 4,
    "limit_decrease": 5,
    "stop_loss_decrease": 6,
    "liquidation": 7,
}

decrease_position_swap_type = {
    "no_swap": 0,
    "swap_pnl_token_to_collateral_token": 1,
    "swap_collateral_token_to_pnl_token": 2,
}


def find_dictionary_by_key_value(outer_dict, key, value):
    for inner_dict in outer_dict.values():
        if key in inner_dict and inner_dict[key] == value:
            return inner_dict
    return None


PRECISION = 30


def apply_factor(value, factor):
    return value * factor / 10**30


def get_funding_factor_per_period(market_info: dict,
                                  is_long: bool,
                                  period_in_seconds: int,
                                  long_interest_usd: int,
                                  short_interest_usd: int,
                                  ):

    funding_factor_per_second = market_info['funding_factor_per_second']*10**-28

    # print(funding_factor_per_second)
    long_pays_shorts = market_info['is_long_pays_short']

    if is_long:
        is_larger_side = long_pays_shorts
    else:
        is_larger_side = not long_pays_shorts

    if is_larger_side:
        factor_per_second = funding_factor_per_second * -1
    else:
        if long_pays_shorts:
            larger_interest_usd = long_interest_usd
            smaller_interest_usd = short_interest_usd

        else:
            larger_interest_usd = short_interest_usd
            smaller_interest_usd = long_interest_usd

        if smaller_interest_usd > 0:
            ratio = larger_interest_usd * 10**30 / smaller_interest_usd

        else:
            ratio = 0

        factor_per_second = apply_factor(ratio, funding_factor_per_second)

    return factor_per_second * period_in_seconds


def save_json_file_to_datastore(filename, data):

    filepath = os.path.join(
        base_dir,
        'data_store',
        filename
    )

    with open(filepath, 'w') as f:
        json.dump(data, f)


def make_timestamped_dataframe(data):

    dataframe = pd.DataFrame(data, index=[0])
    dataframe['timestamp'] = datetime.now()

    return dataframe


def save_csv_to_datastore(filename, dataframe):

    archive_filepath = os.path.join(
        base_dir,
        "data_store",
        filename
    )

    if os.path.exists(archive_filepath):
        archive = pd.read_csv(
            archive_filepath
        )

        dataframe = pd.concat(
            [archive, dataframe]
        )

    dataframe.to_csv(
        os.path.join(
            base_dir,
            "data_store",
            filename
        ),
        index=False
    )


def determine_swap_route(markets, in_token, out_token):

    if in_token == "0xaf88d065e77c8cC2239327C5EDb3A432268e5831":
        gmx_market_address = find_dictionary_by_key_value(
            markets,
            "index_token_address",
            out_token
        )['gmx_market_address']
    else:
        gmx_market_address = find_dictionary_by_key_value(
            markets,
            "index_token_address",
            in_token
        )['gmx_market_address']

    is_requires_multi_swap = False

    if out_token != "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" and \
            in_token != "0xaf88d065e77c8cC2239327C5EDb3A432268e5831":
        is_requires_multi_swap = True
        if out_token == "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f":
            out_token = "0x47904963fc8b2340414262125aF798B9655E58Cd"
        second_gmx_market_address = find_dictionary_by_key_value(
            markets,
            "index_token_address",
            out_token
        )['gmx_market_address']

        return [gmx_market_address, second_gmx_market_address], is_requires_multi_swap

    return [gmx_market_address], is_requires_multi_swap


if __name__ == "__main__":

    output = get_tokens_address_dict('avalanche')
