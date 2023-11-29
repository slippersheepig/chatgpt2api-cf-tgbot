import os
import logging
import schedule
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# 设置日志级别和格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = os.getenv('BASE_URL')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
CF_API_TOKEN = os.getenv('CF_API_TOKEN')
CF_ACCOUNT_ID = os.getenv('CF_ACCOUNT_ID')
CF_SCRIPT_NAME = os.getenv('CF_SCRIPT_NAME')
CF_SCRIPT_VARIABLE_NAME = os.getenv('CF_SCRIPT_VARIABLE_NAME')

def login():
    url = f'{BASE_URL}/chatgpt/login'
    data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        access_token = response.json().get('accessToken')
        return access_token
    else:
        logging.error('登录失败')
        return None

def push_token_to_cloudflare_worker(access_token):
    headers = {
        'Authorization': f'Bearer {CF_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    # 更新 Cloudflare worker 中的变量
    payload = {
        'vars': {
            CF_SCRIPT_VARIABLE_NAME: access_token
        }
    }

    url = f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/workers/scripts/{CF_SCRIPT_NAME}/variable'
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        logging.info('访问令牌成功刷新并推送到 Cloudflare worker')
    else:
        logging.error('访问令牌刷新并推送到 Cloudflare worker 失败')

def refresh_token_and_push():
    access_token = login()
    if not access_token:
        logging.error('登录失败')
        return

    push_token_to_cloudflare_worker(access_token)

def main():
    access_token = login()  # 首次运行立即更新变量
    if access_token:
        push_token_to_cloudflare_worker(access_token)

    schedule.every().week.do(refresh_token_and_push)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
