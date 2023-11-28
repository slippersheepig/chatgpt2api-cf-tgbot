import logging
import requests
import schedule
import time
import os
from dotenv import load_dotenv
import sys
import urllib.parse

load_dotenv()

# 设置日志级别和格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_access_token(host, email, password):
    url = f'http://{host}/auth/token'
    data = {
        'username': email,
        'password': password,
    }
    response = requests.post(url, data=urllib.parse.urlencode(data), headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        logging.error('Failed to get access token')
        return None

def push_token_to_cloudflare_worker(access_token):
    cf_api_token = os.getenv('CF_API_TOKEN')
    account_id = os.getenv('CF_ACCOUNT_ID')
    script_name = os.getenv('CF_SCRIPT_NAME')
    script_variable_name = os.getenv('CF_SCRIPT_VARIABLE_NAME')

    headers = {
        'Authorization': f'Bearer {cf_api_token}',
        'Content-Type': 'application/json'
    }

    # 更新 Cloudflare worker 中的变量
    payload = {
        'vars': {
            script_variable_name: access_token
        }
    }

    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}/variable'
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        logging.info('Token pushed to Cloudflare worker successfully')
    else:
        logging.error('Failed to push token to Cloudflare worker')

def refresh_token_and_push(host, email, password):
    access_token = get_access_token(host, email, password)
    if not access_token:
        logging.error('Failed to get access token')
        return

    url = f'http://{host}/auth/refresh_token'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        push_token_to_cloudflare_worker(access_token)
    else:
        logging.error('Failed to refresh access token')

def main():
    host = os.getenv('HOST')
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    if not host or not email or not password:
        logging.error('Please provide HOST, EMAIL, and PASSWORD in the .env file')
        sys.exit(1)

    # 获取并推送 access_token
    access_token = get_access_token(host, email, password)
    if access_token:
        push_token_to_cloudflare_worker(access_token)
    else:
        logging.error('Failed to get access token')

    # 每周定时刷新并推送 access_token
    schedule.every().week.do(refresh_token_and_push, host=host, email=email, password=password)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
