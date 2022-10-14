# technical-interview-clutch
Тестовое задание для собеседования на Python разработчика

## Developers

Установка проекта
```shell
pipenv install
pipenv shell
```

Создание базы, пользователя и генерация фейковых данных
```shell
cd kontora/
./manage.py migrate
./manage.py fakedata
./manage.py createsuperuser --username=admin
./manage.py runserver
```

## todo:

- Нужно добавить view в котором будет отображать отчет по текущим данным из Debt таблицы
  - Возможно потребуется добавить еще данных в таблицы
- Добавить бенчмарк тест, который покажет что наша задумка удалясь
