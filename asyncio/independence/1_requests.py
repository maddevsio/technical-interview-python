import requests

# Задачи:
#- Нужно написать код, который шлёт запросы в API, который умеет:
# 1. Параллелизировать запросы
# 2. Лимитировать запросы для случаев (когда API сервер может обрабатывать только 10 запросов за раз)
# 3. Выдавать результаты по мере поступления (если один из конкурентных запросов выполнился быстро, то получить его результат)

def read_example(requests_count: int) -> list[int]:
    responses = []

    for _ in range(requests_count):
        response = requests.get('https://www.example.com')
        responses.append(response.status_code)

    return responses
