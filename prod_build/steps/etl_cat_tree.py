import dvc.api
import pandas as pd

params = dvc.api.params_show()


def etl_cat_tree():
    """Category tree data ETL step."""

    assert params['PATH_CSV_CAT_TREE']

    # Загружаем данные из .csv и переименовываем столбцы
    cat_tree = (
        pd.read_csv(params['PATH_CSV_CAT_TREE'])
        .rename(columns={
            'categoryid': 'category_id',
            'parentid': 'parent_id'
        })
    )

    # Проверка на отсутствие дубликатов category_id
    assert cat_tree['category_id'].duplicated().sum() == 0

    # Добалвяем столбец 'parents' с перечнем родителей
    cat_tree['parents'] = pd.NA

    # Получим содержимое таблицы в виде списка кортежей
    # (category_id, parent_id)
    categories = list(cat_tree[['category_id', 'parent_id']]
                      .itertuples(index=False))

    # Временно поменяем индекс таблицы на 'category_id'
    cat_tree.set_index('category_id', inplace=True)

    # Итерируем, пока в списке кортежей есть элементы (необработанне категории)
    while (categories_left := len(categories)):

        # Проходим по копии (!) списка необработанных категорий
        for category_id, parent_id in list(categories):

            # Если категория не является категорией верхнего уровня
            # И ее родительская категория еще не обработана
            # (не размечена в таблице) переходим к следующей
            if (
                pd.notna(parent_id)
                and parent_id not in (
                    cat_tree[cat_tree['parents'].notna()].index
                )
            ):
                continue

            # Для всех категорий, кроме верхнего уровня, список родителей это:
            # родители родителя плюс сам родитель :)
            # А для верхнего уровня список родителей пустой.
            cat_tree.at[category_id, 'parents'] = (
                cat_tree.at[parent_id, 'parents'] + [int(parent_id)]
                if pd.notna(parent_id) else []
            )

            # Удаляем категорию из списка необработанных
            categories.pop(categories.index((category_id, parent_id)))

        # Если после прохода число категорий в списке не уменьшилось
        # то прерываем цикл (битые данные: категории с неизвестными parent_id)
        if len(categories) == categories_left:
            break

    # Возвращаем 'category_id' обратно в столбцы
    cat_tree.reset_index(inplace=True)

    # Перепакуем списки в кортежи
    cat_tree['parents'] = cat_tree['parents'].map(
        lambda x: tuple(x) if isinstance(x, list) else x
    )

    # Проверяем, что обработали все категории
    assert len(categories) == 0

    # Добавляем признак категории верхнего уровня
    cat_tree['top_cat_id'] = (
        cat_tree[['category_id', 'parents']]
        .apply(lambda x: x.parents[0] if x.parents else x.category_id, axis=1)
    )

    # Сохраняем обработанную таблицу локально
    cat_tree.to_parquet('cache/cat_tree.parquet')


if __name__ == '__main__':
    etl_cat_tree()
