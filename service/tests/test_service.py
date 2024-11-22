import json
import os

import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

tests_dir = Path(__file__).parent

# Определяем URI сервиса по настройкам в .env_service
load_dotenv(tests_dir.parent / '.env_service')
service_uri = (
    f"http://{os.getenv('SERVICE_HOST')}:{os.getenv('APP_PORT_EXTERNAL')}"
)

# Загружаем данные запрос/ответ из test_data.json
with open(tests_dir / 'test_data.json', 'r') as f:
    test_data = json.load(f)


# Значение опции 'строгой' проверки ответа
@pytest.fixture(scope='session')
def strict_mode(request):
    return request.config.getoption("--strict-mode")


# Прогоняем тесты из test_data.json
@pytest.mark.parametrize('test', test_data,
                         ids=[x['test_name'] for x in test_data])
def test_unit(test, strict_mode):
    # прогон единичного теста
    response = getattr(requests, test['method'])(
        url=(service_uri + test['uri']),
        headers={'Content-type': 'application/json',
                 'Accept': 'application/json'},
        data=json.dumps(test['data'])
    )
    # Проверка кода ответа
    assert response.status_code == test['response_code']

    # Проверка содержания ответа (если применимо)
    if test.get('response_data'):
        if strict_mode:
            # Полное совпадение ответа с эталоном
            assert response.json() == test['response_data']
        else:
            # Кол-во рекомендаций соответствует ожидаемому
            assert (len(response.json()['recs'])
                    == len(test['response_data']['recs']))
