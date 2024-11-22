import dvc.api
import pandas as pd
import scipy
import threadpoolctl
from implicit.als import AlternatingLeastSquares
from sklearn.preprocessing import LabelEncoder

# Следуем рекомендациям от разработчиков implicit
threadpoolctl.threadpool_limits(1, "blas")

params = dvc.api.params_show()


def build_weighted_als():
    """Build weighted ALS personal recommendations."""

    assert params['N_RECS_USER']
    assert params['RANDOM_STATE']
    assert params['ALS_VIEW_WEIGHT']
    assert params['ALS_ADDTOCART_WEIGHT']
    assert params['ALS_FACTORS']
    assert params['ALS_ITERATIONS']
    assert params['ALS_REGULARIZATION']
    assert isinstance(params['ALS_FILTER_ALREADY_LIKED'], bool)

    # Загружаем прредобработанные данные
    events_train = pd.read_parquet('cache/events_train.parquet')

    # Подготовим таблицу событий для построения матрицы:
    # оставим только события просмора/добалвнеия в корзину,
    # удалим для каждого пользователя дублирующиеся события
    # взаимодействия (с тем же товаром)
    events_train_als = (
        events_train
        .query('event == "addtocart" or event == "view"')
        .drop_duplicates(['user_id', 'event', 'item_id'])
        [['user_id', 'item_id', 'event']]
        .reset_index(drop=True)
    )

    # Добваляем столбец с весами
    # NB: в таблице уже оставлено только два типа событий (view и addtocart)
    events_train_als['weight'] = events_train_als['event'].map(
        lambda x: params['ALS_VIEW_WEIGHT'] if x == 'view'
        else params['ALS_ADDTOCART_WEIGHT']
    ).astype('float32')

    # Создаем энкодеры для перекодирования идентификаторов user_id, item_id
    # в натруральный ряд  {0, 1, ...} для построения матрицы взаимодействий
    user_encoder = LabelEncoder().fit(
        events_train_als['user_id'].drop_duplicates().sort_values()
    )
    item_encoder = LabelEncoder().fit(
        events_train_als['item_id'].drop_duplicates().sort_values()
    )

    # создаём sparse-матрицу (user x item)
    user_item_matrix = scipy.sparse.csr_matrix(
        # кортеж вида (data, (row_index, col_index))
        (
            # Используем разные веса для разных событий
            events_train_als['weight'].to_numpy(),
            (
                user_encoder.transform(events_train_als['user_id']),
                item_encoder.transform(events_train_als['item_id'])
            )
        )
    )

    # Раскладываем матрицу с помощью ALS
    als_model = AlternatingLeastSquares(
        factors=params['ALS_FACTORS'],
        iterations=params['ALS_ITERATIONS'],
        regularization=params['ALS_REGULARIZATION'],
        random_state=params['RANDOM_STATE']
    )
    als_model.fit(user_item_matrix)

    print('Building recs, please wait, this might take a while...')
    # Получаем рекомендации для всех пользователй из обучающей выборки
    als_item_ids, als_scores = als_model.recommend(
        range(len(user_encoder.classes_)),
        user_item_matrix,
        filter_already_liked_items=params['ALS_FILTER_ALREADY_LIKED'],
        N=params['N_RECS_USER']
    )

    # Перепаковываем рекомендации в таблицу формата
    # (user_id, item_id, score)
    personal_als = pd.DataFrame({
        'user_id': range(len(user_encoder.classes_)),
        'item_id': als_item_ids.tolist(),
        'score': als_scores.tolist()
    })
    personal_als = personal_als.explode(
        ['item_id', 'score'], ignore_index=True
    )

    # Приводим типы
    personal_als['user_id'] = personal_als['user_id'].astype('int32')
    personal_als['item_id'] = personal_als['item_id'].astype('int32')
    personal_als['score'] = personal_als['score'].astype('float32')

    # Перекодируем индентификаторы в исходные
    personal_als['user_id'] = (
        user_encoder.inverse_transform(personal_als['user_id'])
    )
    personal_als['item_id'] = (
        item_encoder.inverse_transform(personal_als['item_id'])
    )

    # Сортируем таблицу
    personal_als = personal_als.sort_values(
        by=['user_id', 'score'],
        ascending=[True, False],
        ignore_index=True
    )

    # Сохраняем таблицу локально
    personal_als.to_parquet('recs/weighted_als.parquet')


if __name__ == '__main__':
    build_weighted_als()
