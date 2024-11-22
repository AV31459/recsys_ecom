import dvc.api
import pandas as pd

params = dvc.api.params_show()


def etl_items():
    """Item properties data ETL step."""

    assert params['PATH_CSV_ITEMS1']
    assert params['PATH_CSV_ITEMS2']

    # Загружаем данные из таблиц, переименовываем столбцы
    items = pd.concat([
        pd.read_csv(params['PATH_CSV_ITEMS1']),
        pd.read_csv(params['PATH_CSV_ITEMS2'])
    ]).rename(columns={'itemid': 'item_id'})

    # Из всех значений 'property' оставляем только 'categoryid',
    # приводим 'value' к типу int
    items = (
        items[items['property'] == 'categoryid']
        .astype(dtype={'value': 'int'})
    )

    # Приводим 'timestamp' к типу datetime
    items['timestamp'] = pd.to_datetime(
        items['timestamp'], unit='ms'
    )

    # Удалим столбец 'property', столбец 'value' переименуем в 'category_id'
    items = (
        items
        .drop(columns='property')
        .rename(columns={'value': 'category_id'})
        # Отсортируем таблицу
        .sort_values(by=['item_id', 'timestamp'], ignore_index=True)
    )

    # Загрузим подготовленную таблицу с деревом категорий
    cat_tree = pd.read_parquet('cache/cat_tree.parquet')

    # Добавим в таблицу items признаки 'parents', 'top_cat_id'
    items = items.merge(
        cat_tree[['category_id', 'parents', 'top_cat_id']],
        on='category_id',
        how='inner'
    ).reset_index(drop=True)

    # Сохраняем обработанные таблицы локально
    items.to_parquet('cache/items.parquet')


if __name__ == '__main__':
    etl_items()
