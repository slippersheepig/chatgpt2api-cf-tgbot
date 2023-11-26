import requests
import schedule
import time
import os
from dotenv import load_dotenv

load_dotenv()

def get_access_token(host, email, password):
    url = f'http://{host}/auth/token'
    data = {
        'username': email,
        'password': password,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        print('Failed to get access token')
        return None

def refresh_token_and_push(host, cloudflare_worker_url, email, password):
    access_token = get_access_token(host, email, password)
    if access_token:
        url = f'http://{host}/auth/refresh_token'
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            cfw_token = response.json().get('access_token')
            cf_api_token = os.getenv('CF_API_TOKEN')
            zone_id = os.getenv('CF_ZONE_ID')
            script_name = os.getenv('CF_SCRIPT_NAME')
            script_variable_name = os.getenv('CF_SCRIPT_VARIABLE_NAME')
            
            headers = {
                'Authorization': f'Bearer {cf_api_token}',
                'Content-Type': 'application/json'
            }

            # 更新 Cloudflare worker 中的变量
            payload = {
                'vars': {
                    script_variable_name: cfw_token
                }
            }
            
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/workers/scripts/{script_name}/variable'
            response = requests.put(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print('Token pushed to Cloudflare worker successfully')
            else:
                print('Failed to push token to Cloudflare worker')
        else:
            print('Failed to refresh access token')

def main():
    host = os.getenv('HOST')
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    cloudflare_worker_url = os.getenv('CLOUDFLARE_WORKER_URL')

    if not host or not email or not password or not cloudflare_worker_url:
        print('Please provide HOST, EMAIL, PASSWORD, and CLOUDFLARE_WORKER_URL in the .env file')
        sys.exit(1)
    
    schedule.every().week.do(refresh_token_and_push, host=host, cloudflare_worker_url=cloudflare_worker_url, email=email, password=password)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
