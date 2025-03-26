import json

import requests
import time

# Replace these with your values
API_KEY = 'th3qgA5pAdNc'
PROJECT_TOKEN = 'tBhZqGMT_51q'
RUN_INTERVAL_SECONDS = 3600  # For example: run every hour


def start_run():
    response = requests.post(
        'https://www.parsehub.com/api/v2/projects/{}/run'.format(PROJECT_TOKEN),
        data={
            'api_key': API_KEY,
            'start_url': '',
            'send_email': '0'
        }
    )
    run_data = response.json()
    print("Run started:", run_data)
    return run_data.get('run_token')


def check_run_complete(run_token):
    while True:
        response = requests.get(
            'https://www.parsehub.com/api/v2/runs/{}'.format(run_token),
            params={'api_key': API_KEY}
        )
        run_status = response.json()
        print("Run status:", run_status['status'])
        if run_status['status'] == 'complete':
            return run_status
        time.sleep(10)


def get_run_data(run_token):
    response = requests.get(
        'https://www.parsehub.com/api/v2/runs/{}/data'.format(run_token),
        params={'api_key': API_KEY}
    )
    run_data = response.json()
    print("Run data received.")
    return run_data


r_token = start_run()
if r_token:
    check_run_complete(r_token)
    data = get_run_data(r_token)
    # You can save data or process it here
    with open('./data/run_results.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        print('international data updated!')

else:
    print("Error: Could not start ParseHub run.")
