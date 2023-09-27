## Описание задачи
We need to build a SaaS product in a healthcare sector, which helps users track their sleep.
So, we need 2 applications for users to work with:
* Mobile App
* Web App
Mobile app should collect data about user's sleep (duration, movement, sounds, etc.) and send them to us for:
* Analyzing using ML models
* Preparing stats and analytics
* Also, Mobile App and Web App should display analytics and stats to users.

## Задача
1. 

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
