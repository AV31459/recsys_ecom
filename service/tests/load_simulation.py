import json
import os
import random
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

tests_dir = Path(__file__).parent

# Определяем URI сервиса по настройкам в .env_service
load_dotenv(tests_dir.parent / '.env_service')
service_uri = (
    f"http://{os.getenv('SERVICE_HOST')}:{os.getenv('APP_PORT_EXTERNAL')}/recs"
)

# Максимальное число запросов в одном 'пакете'
MAX_REQUEST_VOLLEY = 1000

# Максимальный таймаут между 'пакетами' запросов (сек)
MAX_TIMEOUT = 30

SEP = '-' * 40 + '\n'

# Загружаем примеры запросов из юнит-тестов
with open(tests_dir / 'test_data.json', 'r') as f:
    test_data = json.load(f)

# Оставим только запросы c валидными данными (проверять стабильность
# сериализации с помощью стандартных методов fastapi/pydantc не будем ;)
valid_requests = [
    json.dumps(test['data']) for test in test_data
    if test['uri'] == '/recs' and test["response_code"] == 200
]

print(f'Taregtng application at: {service_uri}')

while True:
    volley_size = random.randint(0, MAX_REQUEST_VOLLEY)
    print(SEP + f'Running a series of {volley_size} requests... ', end='')

    t_start = time.time()

    for data in random.choices(valid_requests, k=volley_size):
        response = requests.post(
            service_uri,
            headers={'Content-type': 'application/json',
                     'Accept': 'application/json'},
            data=data
        )
        if response.status_code == 200:
            continue
        print('\n Наташа, мы его уронили...')
        print(f'Status code: {response.status_code}', end='')
        print(f'Body: {response.json()}')

    duration = time.time() - t_start

    print(f'done in {duration:.2f}s at {volley_size / duration:.1f} rps')

    sleep_time = random.randint(0, MAX_TIMEOUT)
    print(f'Sleeping for {sleep_time} seconds...')
    time.sleep(sleep_time)
