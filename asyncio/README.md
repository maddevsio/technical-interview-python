# asyncio
Тестовые задания для проверки знания библиотеки asyncio.

## Manual
Есть две вариации первого задания (requests):
* Interactiveness (более быстрая вариация, которая поможет проверить именно основные моменты).
* Independence (более сложная вариация, где кандидату нужно будет писать все с нуля).

#### Independence requests
Задачи:
Нужно написать код, который шлёт запросы в API, который умеет:
1. Параллелизировать запросы
2. Лимитировать запросы для случаев (когда API сервер может обрабатывать только 10 запросов за раз)
3. Выдавать результаты по мере поступления (если один из конкурентных запросов выполнился быстро, то получить его результат)

Вариант решения в самом низу блока "Interactiveness requests".

#### Interactiveness requests
Нам нужно делать N запросов в API, все работает медленно. Как ускорить код используя асинхронность?

Вариант решения:
```python
async def fetch_example(session) -> int:
    async with session.get('https://www.example.com') as response:
        return response.status


async def read_example_async(requests_count: int) -> list[int]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_example(session) for _ in range(requests_count)]
        responses = await asyncio.gather(*tasks)

    return responses
```
Вопросы:
1. Что если одна из тасок поднимет исключение?
2. Как сделать повторные запросы только для тех тасок, которые не завершились?

Теперь мы наш другой сервис (example.com) не выдерживает такую нагрузку. Необходимо уменьшить её.
Вариант решения с помощью семафоров:
```python
async def fetch_example(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
    async with semaphore:
        async with session.get('https://www.example.com') as response:
            return response.status


async def read_example_async(requests_count: int) -> list[int]:
    semaphore = asyncio.Semaphore(10)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_example(session, semaphore) for _ in range(requests_count)]
        responses = await asyncio.gather(*tasks)

    return responses
```
Вопросы:
1. Чем отличается semaphore от bounded semaphore?
2. Что если запросы могут длиться слишком долго и мы бы хотели добавить таймауты. Как это реализовать?

Некоторые запросы выполняются слишком долго и нам нужно возвращать те, которые уже получены как можно раньше. Как этого добиться?
Вариант решения:
```python
async def fetch_example(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> int:
    async with semaphore:
        async with session.get('https://www.example.com') as response:
            return response.status


async def read_example_async(requests_count: int):
    semaphore = asyncio.Semaphore(10)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_example(session, semaphore) for _ in range(requests_count)]

        for coroutine in asyncio.as_completed(tasks):
            response = await coroutine
            some_business_logic(response)
```
Вопросы:
1. Какие у as_completed есть минусы по сравнению с gather?

* #### hashlib
Мы узнали что в базе хранятся незахешированные пароли. И нам нужно срочно захешировать их все.
Пользователей в базе очень много. Даже с нашими мощностями это будет крайне долгая операция.
Как нам ускорить следующий код?
Проблема в том, что hashlib не асинхронный.

Вариант решения:
```python
from concurrent.futures.thread import ThreadPoolExecutor

async def hash_all_passwords() -> list[str]:
    loop = asyncio.get_running_loop()
    tasks = []

    with ThreadPoolExecutor(max_workers=100) as pool:
        for password in passwords:
            tasks.append(loop.run_in_executor(pool, functools.partial(get_hash, password)))

    hashed_passwords = await asyncio.gather(*tasks)
    return hashed_passwords
```
Решение заключается в том, что библиотеки которые написаны на ЯП в которых нет GIL позволяют нам использовать их в тредах.
Кандитат может предложить решение с использованием мультипроцессинга, это тоже валидно. 

Вопросы:
1. Как выбрать оптимальное количество воркеров?
2. Что в этом случае будет эффективней мультипроцессинг или мультитрединг?


* #### sync_primitives
Найти проблему в коде и решить её.
У нас есть параллельная задача, которой нужна копия данных сайта. Сначала она проверит есть ли она в кэше, если есть,
то получит её из кэша, а если нет, то сделает запрос на API.
Проблема в том, что чтения данных занимает некоторое время для возврата и обновления кэша, при одновременном выполнении
нескольких параллельных задач все они предполагают, что этих данных в кэше нет, и делают запросы на API. 
В нашем примере обе таски сделают запрос на API, хотя мы бы хотели, чтобы запрос сделал лишь первый, а второй получил данные из кеша.

Если у кандидата возникнут сложности, то он может попробовать запустить код.
```python
async def get_value(key: str, lock: asyncio.Lock):
    async with lock:
        if key not in cache:
            print(f"The value of key {key} is not in cache")
            value = await request_remote()
            cache[key] = value
        else:
            print(f"The value of key {key} is already in cache")
            value = cache[key]
        print(f"The value of {key} is {value}")
        return value


async def main():
    lock = asyncio.Lock()
    task_one = asyncio.create_task(get_value("status", lock))
    task_two = asyncio.create_task(get_value("status", lock))

    await asyncio.gather(task_one, task_two)
```
Вопросы:
1. ...


## todo:
- Можно накинуть задачку на Condition/Event/BoundedSemaphore.
- В 3.11 появился Barrier, можно придумать задачу на него.