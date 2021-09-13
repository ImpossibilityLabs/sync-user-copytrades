#!/usr/bin/env python3

import configparser
import getpass
import json
import uuid
from typing import List, Dict

import requests

import bitget.mix.order_api as bitget_sdk

default_base_url = 'http://copytrading.xforceglobal.com'
default_symbols = 'BTCUSDT,XRPUSDT,ETHUSDT'
default_hours = 1


# Function to get recent orders from the bitget api.
def send_orders_to_bitget_api(in_base_url: str, in_token: str, in_orders: List, api_key: str, api_secret: str, api_password: str) -> Dict:
    if not api_key:
        raise BaseException('no api key')

    if not api_key:
        raise BaseException('no api secret')

    if not api_password:
        raise BaseException('no api password')

    # Create the api object to perform requests using the API credentials.
    bitget_sdk_order_api = bitget_sdk.OrderApi(api_key, api_secret, api_password, first=False)

    child_orders = []

    for order in in_orders:
        child_order_id = uuid.uuid4().hex

        response: Dict = bitget_sdk_order_api.place_order(symbol=order['symbol'],
                                                          marginCoin=order['marginCoin'],
                                                          size=order['size'],
                                                          side=order['side'],
                                                          orderType=order['orderType'],  # 'market',  # 'market'
                                                          price=order['priceAvg'],
                                                          clientOrderId=child_order_id)

        # response = {"data": {"clientOid": 'test', "orderId": 'test'}, "code": "00000"}

        # Check if request was successful and return data if everything was fine.
        if 'code' in response and int(response['code']) == 0:
            if 'data' in response:
                data = response['data']

                client_oid = ''
                if 'clientOid' in data:
                    client_oid = data['clientOid']
                else:
                    print('failed to get client order id for the placed order')

                order_id = ''
                if 'orderId' in data:
                    order_id = data['orderId']
                else:
                    print('failed to get order id for the placed order')

                child_order = {
                    'id': child_order_id,
                    'symbol': order['symbol'],
                    'size': order['size'],
                    'side': order['side'],
                    'orderId': order_id,
                    'clientOid': client_oid,
                    'filledQty': order['filledQty'],
                    'fee': order['fee'],
                    'price': order['price'],
                    'priceAvg': order['priceAvg'],
                    'state': order['state'],
                    'timeInForce': order['timeInForce'],
                    'totalProfits': order['totalProfits'],
                    'posSide': order['posSide'],
                    'marginCoin': order['marginCoin'],
                    'filledAmount': order['filledAmount'],
                    'ctime': order['ctime'],
                    'orderType': 'market',
                    'parentOrderId': order['id']
                }

                child_orders.append(child_order)


        else:
            print(f"Something went wrong: {response}")

    # Send placed child orders to the api to be stored as placed orders to avoid duplication.
    url = in_base_url + '/orders'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {in_token}'
    }
    api_response = requests.post(url, headers=headers, json={"orders": child_orders})
    api_response_json = api_response.json()

    if api_response.status_code != 200:
        if 'error' in api_response_json:
            raise BaseException(api_response_json['error'])
        raise BaseException('unknown error')
    else:
        print(f'Placed {api_response_json["data"]} new orders')

    return api_response_json


def login(in_base_url: str, in_email: str, in_password: str):
    url = in_base_url + '/login'
    body = json.dumps({"email": in_email, "password": in_password})
    response = requests.post(url, data=body)

    if response.status_code == 200:
        response_json = response.json()
        if 'access_token' in response_json:
            return response_json['access_token']
        else:
            if 'error' in response_json:
                print(f"Failed to authenticate: {response_json['error']}")
            else:
                print(f"Failed to authenticate")

    return None


def get_orders(in_base_url: str, in_token: str, symbols: List[str], hours_past: int = 1):
    url = in_base_url + '/orders' + '?symbols=' + ','.join(symbols)
    if hours_past <= 0:
        hours_past = 1
    if hours_past > 24 * 7:
        hours_past = 24 * 7
    url = url + f'&hours_past={hours_past}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {in_token}'
    }
    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response.status_code != 200:
        if 'error' in response_json:
            raise BaseException(response_json['error'])
        raise BaseException('unknown error')

    return response_json


class Configuration:
    bitget_api_key: str
    bitget_api_secret: str
    bitget_api_password: str
    email: str
    password: str
    past_hours: int
    base_url: str
    symbols: str


def parse_configuration() -> Configuration:
    section = 'default'
    config_parser = configparser.ConfigParser()
    files = config_parser.read("config.ini")
    cfg = Configuration()
    if len(files) > 0:
        if section in config_parser.sections():
            cfg.bitget_api_key = config_parser[section]['bitget_api_key']
            cfg.bitget_api_secret = config_parser[section]['bitget_api_secret']
            cfg.bitget_api_password = config_parser[section]['bitget_api_password']
            cfg.email = config_parser[section]['email']
            cfg.password = config_parser[section]['password']
            cfg.past_hours = config_parser[section]['past_hours']
            cfg.base_url = config_parser[section]['base_url']
            cfg.symbols = config_parser[section]['symbols']
    else:
        cfg.bitget_api_key = ''
        cfg.bitget_api_secret = ''
        cfg.bitget_api_password = ''
        cfg.email = ''
        cfg.password = ''
        cfg.past_hours = 0
        cfg.base_url = ''
        cfg.symbols = ''

    return cfg


if __name__ == '__main__':
    config = parse_configuration()

    # Get desired symbols to read orders from the user.
    if not config.symbols:
        print(f'Enter symbols to read from the bitget, comma divided. Default is [{default_symbols}].')
        symbol_string = input()
        if symbol_string and not symbol_string.replace(',', '').isalpha():
            print('Invalid symbol list has been provided. Symbol list should be list of coin pairs divided with comma. Exiting.')
            exit(1)
        config.symbols = symbol_string

    # Fallback to default symbols if none were provided.
    if not config.symbols:
        config.symbols = default_symbols

    # Convert string of comma-separated symbols into a list.
    symbols = config.symbols.split(',')

    # Convert symbols to unified margin api symbols appending the suffix.
    for i, s in enumerate(symbols):
        symbols[i] = s + '_UMCBL'

    # Get the base URL.
    if not config.base_url:
        print(f'Enter the base api URL. Default is [{default_base_url}]')
        base_url = input()
        if not base_url:
            config.base_url = default_base_url
        if not base_url.startswith('http'):
            print('Invalid URL scheme. Must be http or https. Exiting.')
            exit(1)
        config.base_url = base_url

    # Enter backend API email.
    if not config.email:
        print('Please enter the email:')
        config.email = input()
        if not config.email:
            print('Invalid email. Exiting.')

    # Enter backend API password.
    if not config.password:
        print('Please enter the password:')
        config.password = getpass.getpass('Password:')
        if not config.password:
            print('Invalid password. Exiting.')

    # Get the backend API token.
    access_token = login(in_base_url=config.base_url, in_email=config.email, in_password=config.password)

    if not access_token:
        print(f"Authentication failed. Exiting.")
        exit(1)

    print(f"Authenticated, getting orders...")

    # Get the past hours value.
    if not config.past_hours:
        print(f'Enter past hours to read symbols from and until now. Default is [{default_hours}].')
        hours_string = input()
        if hours_string:
            config.past_hours = int(input())
        else:
            config.past_hours = default_hours
    else:
        config.past_hours = int(config.past_hours)

    # Send orders to the copy-trade backend.
    orders: Dict = {'data': []}
    try:
        orders = get_orders(in_base_url=config.base_url, in_token=access_token, symbols=symbols, hours_past=config.past_hours)
    except BaseException as e:
        print(f"Failed to receive orders: {e}. Exiting.")
        exit(1)

    if ('data' in orders and len(orders['data'])) > 0:
        print(f"Received {len(orders['data'])} orders.")
    else:
        print(f"Received no new orders to copy. Exiting.")
        exit(1)

    # Get the bitget api key from the user.
    if not config.bitget_api_key:
        print('Enter the bitget api key:')
        bitgetApiKey = input()
        if not bitgetApiKey:
            print('No bitget api key or invalid api key has been provided. Exiting.')
            exit(1)
        config.bitget_api_key = bitgetApiKey

    # Get the bitget api secret from the user.
    if not config.bitget_api_secret:
        print('Enter the bitget api secret:')
        bitgetApiSecret = input()
        if not bitgetApiSecret:
            print('No bitget api secret or invalid api secret has been provided. Exiting.')
            exit(1)
        config.bitget_api_secret = bitgetApiSecret

    # Get the bitget api password from the user.
    if not config.bitget_api_password:
        print('Enter the bitget api password:')
        bitgetApiPassword = input()
        if not bitgetApiPassword:
            print('No bitget api password or invalid api password has been provided. Exiting.')
            exit(1)
        config.bitget_api_password = bitgetApiPassword

    # Place orders.
    print('Please wait, placing new orders...')
    status = send_orders_to_bitget_api(in_base_url=config.base_url, in_token=access_token, in_orders=orders['data'],
                                       api_key=config.bitget_api_key,
                                       api_secret=config.bitget_api_secret,
                                       api_password=config.bitget_api_password)

    del config.bitget_api_key
    del config.bitget_api_secret
    del config.bitget_api_password
