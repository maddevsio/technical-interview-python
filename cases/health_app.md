## Описание задачи
We need to build a SaaS product in a healthcare sector, which helps users track their sleep.
There are 2 applications for users to work with:
* Mobile App
* Web App
Mobile app collects data about user's sleep (duration, movement, sounds, etc.) and sends it to the backend. Backend performs following:
* Analyze sleep data using ML models (Input: duration, movement, sounds)
* Prepare analytics on a sleep data
* Persists analytics and raw data
* Serves analytics to users (API endpoints, Dashboard)

## Задача
1. Упор делаем на бэкенд, мобильное приложение - это клиент
2. Описать архитектуру решения
3. Описать плюсы/минусы решения
4. Как должна выглядеть схема данных на выходе из ML-модели?

## На что обращаем внимание:
1. Умеет ли кандидат работать с ML-моделями (training, inference)
2. Знает ли про очереди сообщений - Kafka, RabbitMQ, redis
3. Сталкивался ли с batch/streaming data processing (Apache Spark, Apache Airflow, etc.)
4. Знает ли про объектные хранилища - S3
5. Как кандидат будет делать балансировку нагрузки и как подойдет к масштабированию?
6. Знаком ли кандидат с распределенными вычислениями и оркестрацией (для кейсов когда нужно чейнить несколько сервисов - saga и т.д.)

## Пояснения
1. Лучше статику сразу хранить в s3, потому что огромный массив данных в БД будет тормозить запросы, миграции, бэкапы и т.д.
2. Т.к. МЛ-моделька работать будет не быстро, то всё равно нужно добавлять очереди сообщений, чтобы балансировать нагрузку между воркерами (несколько инстансов МЛ-моделей) и отдавать результаты по мере их готовности (event-driven архитектура)
3. Можно также использовать websocket-ы чтобы не тащить очереди сообщений, но тогда необходимо балансировку нагрузки выносить в отдельный сервис
4. 
