import requests

# Задача:
# Нам нужно делать N запросов в API. Этот код работает медленно. Как ускорить этот код используя асинхронность?

def read_example(requests_count: int) -> list[int]:
    responses = []

    for _ in range(requests_count):
        response = requests.get('https://www.example.com')
        responses.append(response.status_code)

    return responses
