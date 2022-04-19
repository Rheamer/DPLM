# Console client for interaction with rest server
from ast import Index
from calendar import c
from getpass import getpass
from http import server
import sys
from typing import Protocol
import requests as r
import os
session_file = 'session'
  
  
def print_help():
    print('Commands examples:')
    print('getdev - get device list')
    print('swnet - switch network for a group of devices')
    print('blink - blink on board led of a microcontroller')

def check_auth_token(token:str, url:str):
    headers = {'Authorization':f'Token {token}'}
    response = r.request(url=url, method='GET', headers = headers)
    print(response, url)
    return response.status_code == 200

def get_token(url, user, password) -> str:
    payload = {'username':user, 'password':password}
    response = r.request(
        url = url, 
        method = 'POST', 
        data = payload)
    print(response.status_code)
    return response.json()['auth_token']


def main():
    server_debug = True
    if server_debug:
        protocol = 'http:'
    else:
        protocol = 'https:'
    with open(session_file, 'a') as s_file:
        pass
    with open(session_file, 'r') as s_file:
        auth_token = s_file.readline()
        print(auth_token)

    server_address = '127.0.0.1:8000'
    cmd = []
    host = '127.0.0.1'
    if (len(sys.argv) >= 2):
        if str(sys.argv[1]) == '-a' and len(sys.argv) >= 3:
            host = server_address = str(sys.argv[2])
            if server_address.find('.com') == -1:
                server_address += '.com'
            cmd = sys.argv[3:]
        elif str(sys.argv[1]) == '-h':
            print_help()
            return 0
        else:
            cmd = sys.argv[1:]

    if not check_auth_token(auth_token, f'{protocol}//{server_address}/auth/users/me/'):
        username = input('Username:')
        password = getpass('Password:')
        auth_token = get_token(
            f'{protocol}//{server_address}/auth/token/login/', 
            username, password)
        with open(session_file, 'w') as s_file:
            s_file.write(auth_token)

    # 'username': username, 'password': password,
    method = target = ''
    headers = {
        'Authorization' : f'Token {auth_token}',
        'Accept': 'application/json', 
        'host': host}
    try:
        if cmd[0] == 'exit':
            return 0

        elif cmd[0] == 'getdev':
            target = '/devices/list'
            method = 'GET'

        elif cmd[0] == 'swnet':
            target = '/config/net/switch'
            method = 'POST'
            headers['clientID'] = cmd[1]
            headers['wifiSsid'] = cmd[2]
            headers['wifiPass'] = cmd[3]

        elif cmd[0] == 'monitor':
            target = f'/action/stream/{cmd[1]};{cmd[2]}'
            # cmd[1] = clientID
            # cmd[2] = endpoint
            os.system('py sensor_monitor.py ' + server_address + target)
            return 0
                    
        elif cmd[0] == 'act_u':
            target = f'/action/update/{cmd[1]}'
            method = 'UPDATE'
            headers['endpoint'] = cmd[2]
            # NO PAYLOAD IS PAYLAOD ECK ECK ECK ECK ECK ECK
            headers['payload'] = cmd[3]
        
        elif cmd[0] == 'act_p':
            target = f'/action/put/{cmd[1]}'
            method = 'POST'
            headers['endpoint'] = cmd[2]
            headers['payload'] = cmd[3]
        
        elif cmd[0] == 'act_r':
            target = f'/action/read/{cmd[1]}'
            method = 'GET'
            headers['endpoint'] = cmd[2]

    except IndexError:
        print(' '.join(['Error parsing command!', method, target]))
    try:
        # print(server_address)
        # print(target)
        # print(method)
        # print(headers)
        response = r.request(
            # no secure connection locally
            url = f'{protocol}//{server_address}{target}', 
            method = method, headers=headers)
        print(response.text)
    except r.RequestException as e:
        print('Error sending request: ' + str(e))

if __name__ == "__main__":
    main()
