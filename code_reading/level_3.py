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


def reset_user_password(user: User):
    to_hash = f"{time.time()}{user.get_username()}".encode("utf-8")
    reset_token = hashlib.md5(to_hash).hexdigest()

    # Django's User model don't have reset_token field for let's assume it does.
    user.reset_token = reset_token
    user.save()

    # send reset_token to user via email
