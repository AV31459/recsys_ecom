import dvc.api
import pandas as pd

build_date = dvc.api.params_show('build_date.yaml')


def train_test_split():
    """Split events/items tables to train/test."""

    assert build_date['build_date']

    # Временная точка разделения выборок
    SPLIT_DATETIME = pd.to_datetime(build_date["build_date"])

    print(f'Train/test split date: {SPLIT_DATETIME}')

    # Загружаем предобработанные данные
    items = pd.read_parquet('cache/items.parquet')
    events = pd.read_parquet('cache/events.parquet')

    # Сортируем по времени
    items.sort_values('timestamp', ignore_index=True, inplace=True)
    events.sort_values('timestamp', ignore_index=True, inplace=True)

    # Разбиваем события на обучающую и тестовую выборки
    events_train = events[events['timestamp'] < SPLIT_DATETIME]
    events_test = events[events['timestamp'] >= SPLIT_DATETIME]

    # Каталог товаров для обучения модели
    items_train = (
        items[items['timestamp'] < SPLIT_DATETIME]
        .sort_values(by='timestamp', ascending=True)
        .groupby('item_id')
        .tail(1)  # оставляем только последнее значение признака
        .reset_index(drop=True)
    )

    # Удалим из обучающей выборки события для товаров, которые отсутствуют
    # в 'обучающем' какталоге товаров, т.е. свойства которых неизвестны
    # на момент обучения модели
    events_train = (
        events_train[
            events_train['item_id']
            .isin(items_train['item_id'].drop_duplicates())
        ]
        .reset_index(drop=True)
    )

    # Сохраняем таблицы локально
    events_train.to_parquet('cache/events_train.parquet')
    events_test.to_parquet('cache/events_test.parquet')
    items_train.to_parquet('recs/items_train.parquet')


if __name__ == '__main__':
    train_test_split()
