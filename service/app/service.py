import logging
import os
import sys
from contextlib import asynccontextmanager

import requests
from core import RecSysHandler, RecSysRequest, RecSysResponse
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

load_dotenv('.env_service')

# Настраиваем логгер
logger = logging.getLogger('recsys_service')
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(
    logging.Formatter(
        '%(levelname)s:\t%(name)s:  %(asctime)s : %(message)s'
    )
)
logger.addHandler(log_handler)
logger.setLevel(os.getenv('APP_LOG_LEVEL'))
logger.info('Recsys service module is being initialized.')

# Основной объект-хендлер для получения рекомендаций
recsys_handler = RecSysHandler(
    path_recs_top_popular=os.getenv('PATH_RECS_TOP_POPULAR'),
    path_recs_personal=os.getenv('PATH_RECS_PERSONAL'),
    path_items_train=os.getenv('PATH_ITEMS_TRAIN'),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    recsys_handler.load_data()
    logger.info('RecSysHandler data loaded, ready to serve requests.')
    yield
    logger.info('Recsys service is being shut down.')


# Основной объект приложения
app = FastAPI(title="Recommendation service", lifespan=lifespan)

# Иструментатор для метрик
Instrumentator().instrument(app).expose(app)

# Метрика: счетчик необработанных исключений
metric_recommend_exception_counter = Counter(
    'app_recsys_handler_exception_counter',
    'Number of unhandled exceptions in recsys_handler'
)


# Healthcheck URI
@app.get('/')
def healthcheck():
    """Get service health status."""

    logger.debug('Healthchek handler called')
    return 'Service appears to be up and running.'


# Основной URI сервиса
@app.post('/recs', response_model=RecSysResponse)
def recommend(request: RecSysRequest):
    """Get recommendations."""

    logger.debug(f'Valid request received: {request}')

    try:
        #  Передаем паремтры в хендлер и получаем рекомендации
        response = RecSysResponse(recs=recsys_handler.get_recs(
            user_id=request.user_id,
            n_recs=request.n_recs,
            last_items=request.last_items
         ))

        logger.debug(f'Sending back response: {response}')

        return response

    except Exception as exc:

        # Увеличиваем счетчик исключений
        metric_recommend_exception_counter.inc()

        logger.error(
            f'Unhandled exception in recsys_handler.get_recs(): {exc}',
            exc_info=True
        )

        raise HTTPException(
            status_code=requests.codes['/o\\'],
            detail='Internal server error'
        )


logger.info('Recsys service module initialization completed.')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv('SERVICE_HOST'),
        port=int(os.getenv('APP_PORT_EXTERNAL')),
    )
