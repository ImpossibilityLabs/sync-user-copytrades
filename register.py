#!/usr/bin/env python3

import getpass
import json

import requests

base_url = 'http://hackerman.me:8000'


def register(in_base_url: str, in_email: str, in_password: str):
    url = in_base_url + '/register'
    body = json.dumps({"email": in_email, "password": in_password})
    response = requests.post(url, data=body)
    response_json = response.json()

    if response.status_code == 200:
        if 'access_token' in response_json:
            return response_json['access_token']

    if 'error' in response_json:
        print(f"Failed to register: {response_json['error']}")
    else:
        print(f"Failed to register")

    return None


if __name__ == '__main__':
    # Enter backend API email.
    print('Please enter email:')
    email = input()
    if not email:
        print('Invalid email. Exiting.')

    # Enter backend API password.
    print('Please enter the password:')
    password = getpass.getpass()
    if not password:
        print('Invalid password. Exiting.')

    # Enter backend API password.
    print('Please confirm the password:')
    password_confirmation = getpass.getpass()
    if not password_confirmation or not password == password_confirmation:
        print('Password confirmation does not match the password. Exiting.')

    result = register(in_base_url=base_url, in_email=email, in_password=password)

    if result:
        print('Registered successfully')
