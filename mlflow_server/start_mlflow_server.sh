#!/bin/bash

[ ! -f ./.env ] || export $(grep -v '^#' ./.env | xargs)

# Cleanup - чистим удаленные запуски из базы/хранилища
mlflow gc \
    --backend-store-uri postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

# NB: --registry-store-uri в нашей конфигурации не нужен
mlflow server \
    --backend-store-uri postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME \
    --default-artifact-root s3://$S3_BUCKET_NAME \
#    --no-serve-artifacts
