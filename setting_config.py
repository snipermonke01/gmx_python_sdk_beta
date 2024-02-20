#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 20:10:00 2024

@author: snipermonke01
"""

from scripts.v2.gmx_utils import Config, get_config

# or omit argument to save/load config in base directory
config_obj = Config()

# Try load config, will create base template if it doesnt exist
new_config_dict = config_obj.load_config()

# overwrite dict values
new_config_dict['arbitrum']['rpc'] = "rpc_url"
new_config_dict['avalanche']['rpc'] = "rpc_url"
new_config_dict['private_key'] = "private_key"
new_config_dict['user_wallet_address'] = "user_wallet_address"

# Set config file
config_obj.set_config(new_config_dict)

# once set, you can use get_config to load directionary of config params
get_config()
