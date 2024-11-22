import dvc.api
import pandas as pd

params = dvc.api.params_show()


def build_top_popular():
    """Build top popular recommendations."""

    assert params['N_RECS_USER']

    # Загружаем прредобработанные данные
    events_train = pd.read_parquet('cache/events_train.parquet')
    items_train = pd.read_parquet('recs/items_train.parquet')

    # Топ популярных по добавлениям в корзину
    top_popular = (
        events_train
        .query('event == "addtocart"')
        .groupby('item_id')
        .agg(score=('user_id', 'count'))
        .reset_index()
        .sort_values(by='score', ascending=False, ignore_index=True)
    )
    top_popular['score'] /= top_popular['score'].max()
    top_popular['score'] = top_popular['score'].astype('float32')

    # Добавляем признак категории товара
    top_popular = top_popular.merge(
        items_train[['item_id', 'category_id']],
        on='item_id',
        how='left'
    )

    assert not top_popular['category_id'].hasnans

    # Сохраняем таблицы локально
    top_popular.to_parquet('recs/top_popular.parquet')


if __name__ == '__main__':
    build_top_popular()
