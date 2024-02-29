import requests
import hashlib
from django.contrib.auth.models import User
import time


# Comment on every function
# - Is there any problem?
# - How does it work?
# - What would be return result?

def get_user_from_api(user_id: int) -> dict | None:
    response = requests.get(f"http://127.0.0.1:8000/user/{user_id}")
    if response.status_code != 200:
        return None

    return response.json()


def calculate_salary(employee):
    if employee.department == "Engineering":
        if employee.experience >= 5:
            salary = employee.base_salary * 1.2
        else:
            salary = employee.base_salary * 1.1
    elif employee.department == "Marketing":
        if employee.experience >= 3:
            salary = employee.base_salary * 1.15
        else:
            salary = employee.base_salary * 1.05
    elif employee.department == "HR":
        if employee.experience >= 2:
            salary = employee.base_salary * 1.1
        else:
            salary = employee.base_salary
    else:
        salary = employee.base_salary * 1.05

    return salary


def reset_user_password(user: User):
    to_hash = f"{time.time()}{user.get_username()}".encode("utf-8")
    reset_token = hashlib.md5(to_hash).hexdigest()

    # Django's User model don't have reset_token field for let's assume it does.
    user.reset_token = reset_token
    user.save()

    # send reset_token to user via email
