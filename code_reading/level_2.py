from django.contrib.auth.models import User


# Comment on every function
# - Is there any logic issues?
# - How does it work?
# - What would be return result?

def get_user_name(user: User | None):
    # 1. user=None
    # 2. user=User(first_name="Joe", last_name="Dickinson")
    # 3. user=User(username="", first_name="Joe", last_name="Dickinson")
    # 4. user=User(username="j_dickinson", first_name="Joe", last_name="Dickinson")
    return user and (user.get_full_name() or user.get_username())


def user_string(data: dict) -> str:
    name = ""
    try:
        name += data["first_name"]
        name += data["last_name"]

        name += " " + data["age"] + "years old."
    except Exception:
        pass

    return name
