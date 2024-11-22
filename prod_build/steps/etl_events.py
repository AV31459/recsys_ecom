import dvc.api
import pandas as pd

params = dvc.api.params_show()


def etl_events():
    """Events ETL step."""

    assert params['PATH_CSV_EVENTS']

    # Загрузим таблицу с каегориями товаров с предыдущего шага
    items = pd.read_parquet('cache/items.parquet')

    events = (
        pd.read_csv(params['PATH_CSV_EVENTS'])
        .rename(columns={
            'visitorid': 'user_id',
            'itemid': 'item_id',
            'transactionid': 'transaction_id'
        })
        .sort_values(by='timestamp', ignore_index=True)
    )

    # Приведем timestamp к типу datetime
    events['timestamp'] = pd.to_datetime(events['timestamp'], unit='ms')

    # Удалим из таблицы событий товары, отсутствующие в каталоге items
    events = events[
        events['item_id'].isin(items['item_id'].drop_duplicates())
    ].reset_index(drop=True)

    # Сохраняем обработанную таблицу локально
    events.to_parquet('cache/events.parquet')


if __name__ == '__main__':
    etl_events()
