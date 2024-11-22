#!/bin/bash

[ ! -f ./.env ] || export $(grep -v '^#' ./.env | xargs)

mlflow gc \
    --backend-store-uri postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
