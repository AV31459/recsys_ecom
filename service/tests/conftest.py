# Добавляем pytest кастомную опцию командной строки
def pytest_addoption(parser):
    parser.addoption('--strict-mode', action='store_true',
                     help='Strict response check mode')
