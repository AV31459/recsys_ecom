import logging
from itertools import zip_longest

import pandas as pd
from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt


class RecSysRequest(BaseModel):
    """Pydantic model of incoming recommendations request."""

    user_id: NonNegativeInt = Field(..., description='User ID')
    n_recs: PositiveInt = Field(10, description='Number of recommendations')
    last_items: list[NonNegativeInt] = Field(
        [], description='Ids of last items user interacted with in '
        'chronological order (the latest is the last)'
    )


class RecSysResponse(BaseModel):
    """Pydantic model of outgoing recsys response."""

    recs: list[NonNegativeInt] = Field(
        ..., description='Ids of recommended items'
    )


class RecSysHandler:
    """
    Main handler class for recommendations retreival.

    Attributes:
        - **path_recs_top_popular** - path to a .parquet file with
        pre-calculated non-personalised recommendations: a table with columns
        (item_id, score, category_id)

        - **path_recs_personal** - path to a .parquet file with pre-calculated
        personalised recommendations: a table with columns
        (user_id, item_id, score)

        - **path_items_train** - path to a .parquet file with items catalog
        containing columns (item_id, category_id)
    """

    def __init__(
        self,
        path_recs_top_popular: str,
        path_recs_personal: str,
        path_items_train: str
    ):
        self.path_recs_top_popular = path_recs_top_popular
        self.path_recs_personal = path_recs_personal
        self.path_items_train = path_items_train
        self.logger = logging.getLogger('recsys_service')

    def load_data(self):
        """Load pre-calculated offline recommendations to memory."""

        self.logger.info(
            f'Loading items_train from: {self.path_items_train}'
        )

        # Загружаем каталог товаров на котором считались рекомендации,
        # преобразуем в словарь формата {item_id: category_id, ...}
        self._item_cats = (
            pd.read_parquet(self.path_items_train)
            .set_index('item_id')
            ['category_id']
            .to_dict()
        )

        self.logger.info(
            f'Loading top-popular recs from: {self.path_recs_top_popular}'
        )

        # Загружаем топ-популярные рекомендации в формате
        # (item_id, score, category_id)
        # NB: устанавливаем category_id как индекс, храним
        # глобально отсортированным по убыванию score
        self._top_popular = (
            pd.read_parquet(
                self.path_recs_top_popular,
                columns=['item_id', 'score', 'category_id']
            )
            .sort_values(by='score', ascending=False)
            .set_index('category_id')
        )

        self.logger.info(
            f'Loading personal recs from: {self.path_recs_personal}'
        )

        # Загружаем персональные рекомендации в формате
        # (user_id, item_id, score),
        # NB: устанавливаем user_id как индекс, для каждого
        # пользователя строки отсортрованы по убыванию score
        self._personal_recs = (
            pd.read_parquet(
                self.path_recs_personal,
                columns=['user_id', 'item_id', 'score']
            )
            .sort_values(by=['user_id', 'score'], ascending=[True, False])
            .set_index('user_id')
        )

        # Формируем set() пользователей, имеющих персональные рекомендации
        self._users_with_personal_recs = set(
            self._personal_recs.index.drop_duplicates()
        )

    def _get_top_popular(
        self,
        n_recs: int,
        category_id: int | None,
    ) -> list[int]:
        """Get top-popular by category or globaly if _category_id_ is None."""

        if category_id is None:
            # Топ-популярные по всем категориям
            return self._top_popular['item_id'].head(n_recs).tolist()

        return (
            self._top_popular.loc[category_id, 'item_id'].head(n_recs).tolist()
        )

    def _get_online_recs(
            self,
            n_recs: int,
            last_items: list[int]
    ) -> list[int]:
        """Get online recommendations based on last items seen online."""

        # Топ-популярные по всем категорям
        top_popular_items = self._get_top_popular(n_recs, category_id=None)

        # Если нет последних просмотренных - отдаем глобальный топ
        if not last_items:
            return top_popular_items

        # Получаем список трех последних просмотренных категорий в обратном
        # порядке (начиная с последней просмотренной)
        last_categories = [self._item_cats.get(item)
                           for item in reversed(last_items[-3:])]

        # Удаляем из списка последних категорий возможные дубликаты / пропуски
        last_categories = (
            pd.Series(last_categories).dropna().drop_duplicates().tolist()
        )

        # Каждую категорию в списке преобразуем в список топ-популярных
        # товаров в этой категории. В конец полученномого списка (из списков)
        # добавляем глобальный топ.
        list_of_lists = (
            [self._get_top_popular(n_recs, category_id)
             for category_id in last_categories]
            + [top_popular_items]
        )

        # Объединяем все товары из списка списков топ-популярных
        # путем чередования:
        # первый из первого списка, первый из второго списка, ...
        # второй из первого списка, второй из второго списка и т.д.
        online_recs = [item for items_tuple in zip_longest(*list_of_lists)
                       for item in items_tuple if item is not None]

        # Удаляем возможные дубликаты, обрезаем до n_recs и отдаем
        return pd.Series(online_recs).drop_duplicates().head(n_recs).tolist()

    def get_recs(
            self,
            user_id: int,
            n_recs: int,
            last_items: list[int]
    ) -> list[int]:
        """Get list of recommendations."""

        # Онлайн рекомендации есть всегда: если не было последних просмотров -
        # получим топ-популярные по всем категорям
        online_recs = self._get_online_recs(n_recs, last_items)

        # Если нет персональных - отдаем онлайн рекомендации
        if user_id not in self._users_with_personal_recs:
            return online_recs

        # Персональные рекомендации (коллаборативыне оффлайн)
        personal_recs = (
            self._personal_recs.loc[user_id, 'item_id'].head(n_recs).tolist()
        )

        # Объединяем два списка путем чередования онлайн и персональных
        final_recs = [x for pair in zip_longest(online_recs, personal_recs)
                      for x in pair if x is not None]

        # Удаляем возможные дубликаты, обрезаем до n_recs и отдаем
        return pd.Series(final_recs).drop_duplicates().head(n_recs).tolist()
