import requests
from django.contrib.auth.models import User

# Comment on every function
# - Is there any problem?
# - How does it work?
# - What would be return result?


def append(number: int, number_list: list[int] = []) -> list[int]:
    number_list.append(number)
    return number_list


def get_user_name(user: User | None):
    # 1. user=None
    # 2. user=User(first_name="Joe", last_name="Dickinson")
    # 3. user=User(username="", first_name="Joe", last_name="Dickinson")
    # 4. user=User(username="j_dickinson", first_name="Joe", last_name="Dickinson")
    return user and (user.get_full_name() or user.get_username())


def get_user_from_api(user_id: int) -> dict | None:
    response = requests.get(f"http://127.0.0.1:8000/user/{user_id}")
    if response.status_code != 200:
        return None

    return response.json()
