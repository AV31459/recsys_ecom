#!/bin/bash

# Переходим в директорию скрипта
cd $(dirname $0)

# Парсим файл с переменными окружения для сервиса
export $(grep -v '^#' .env_service | xargs)

uvicorn --app-dir=app --host=$SERVICE_HOST --port=$APP_PORT_EXTERNAL --reload \
service:app
