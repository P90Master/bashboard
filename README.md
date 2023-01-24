# bashboard
## Описание
Анонимный форум, выполненный в стилистике bash-консоли:
- В его основе лежит древовидная структура тредов:
    - Каждый узел является тредом, который может содержать как сообщения (листья), так и вложенные треды (другие узлы). Такой подход отсылает к файловой системе (тред - папка, сообщение - файл).
- Строка ввода - единственный интерфейс:
    - Отстутсвие каких-либо кнопок: навигация, перемещение, создание и удаление тредов выполняются при помощи "консольных" команд.
- Внешний вид форума схож с внешним видом командной строки.
## Технологии
### Бекенд
- Python 3.9.6
- Flask 2.2.2
- SQLAlchemy 1.4.44
- Python-Socket.IO 5.7.2
- Jinja2 3.1.2
### Фронтенд
- Bootstrap 5.2.3
- jQuery 3.6.3
- Socket.IO 4.5.4
### Инфраструктура
- Docker 20.10.12 (Docker Compose 1.29.2)
- Образ PostgreSQL 15.1 для Docker
## Запуск проекта
- Склонировать репозиторий
- Перейти в папку /infra
- Создать и заполнить .env файл по примеру:
    ```
    SECRET_KEY=<КЛЮЧ>
    DB_NAME=postgres
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=88880000
    DB_HOST=db
    DB_PORT=5432
    ```
- Запустить сборку контейнеров:
    ```
    docker-compose up -d --build
    ```
- Для хранения деревьев использовалось расширение PostgreSQL [Ltree](https://www.postgresql.org/docs/current/ltree.html). Для его загрузки в созданную БД необходимо войти в контейнер с Postgres:
    ```
    sudo docker exec -it bashboard_db bash
    ```
- Далее нужно под суперпользователем войти в БД postgres через psql и создать расширение ltree:
    ```
    su - postgres
    ```
    ```
    psql postgres
    ```
    ```
    CREATE EXTENSION IF NOT EXISTS ltree;
    ```
- Чтобы удостовериться, что расширение ltree включено, можно проверить системный каталог:
    ```
    SELECT * FROM pg_catalog.pg_extension;
    ```
    ltree должно быть в списке и находиться в публичном пространстве имен (extnamespace 2200)
- Выйти из папки /infra и перейти в папку /bashboard
- Далее нужно создать репозиторий миграций:
    ```
    flask db init
    ```
- Перед тем как сгенерировать первые миграции для работы ltree необходимо добавить импорт sqlalchemy_utils в шаблон mako:
    ```
    # /migrations/script.py.mako

    import sqlalchemy_utils
    ```
- Сгенерировать миграции:
    ```
    flask db migrate
    ```
- Применить миграции к базе данных:
    ```
    flask db upgrade
    ```
- Перед тем как запустить проект необходимо создать корневой тред. Для этого нужно запустить интерпретатор shell:
    ```
    flask shell
    ```
- В оболочке shell выполнить следующую программу:
    ```
    main = Thread('main')
    db.session.add(main)
    db.session.commit()
    ```
    Нулевой тред должен инициализироваться с аргументом 'main' и никак иначе.
- Запустить проект:
    ```
    flask run
    ```
## Использование
- Сайт доступен по стандартному адресу http://127.0.0.1:5000
### Команды
Все команды начинаются со слеша "/".
- /: Очищает вывод других команд
- /clear: Очищает доску
- /help [команда]: Информация по конкретной команде / Информация обо всех командах
- /ls [путь]: Выводит список тредов, вложенных в выбранный тред (по умолчанию текущий)
- /cd [путь]: Смена треда (по умолчанию на корневой)
- /mkdir [путь/]<название_нового_треда>: Создание нового треда
- /rmdir <[путь_к_треду/]тред>: Удаление треда
- /get <id>: Получение сообщения по id

Обработка путей:
- "/" в начале - абсолютный путь, иначе - относительный
- ".." - шаг назад
- Поддержка сложных выражений "тред_1/../тред_2/../../тред_3/" и др.