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


def validate_data(data):
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if 'name' in item:
                    name = item['name']
                    if name:
                        if len(name) < 3:
                            raise Exception("Error: Name must be at least 3 characters long!")
                        elif len(name) > 50:
                            raise Exception("Error: Name cannot exceed 50 characters!")
                        elif not name.isalpha():
                            raise Exception("Error: Name must contain only alphabetic characters!")
                        else:
                            raise Exception(f"Processing name: {name}")
                    else:
                        raise Exception("Error: Empty name provided!")
                else:
                    raise Exception("Error: Name key not found in dictionary!")
            else:
                raise Exception("Error: Input data must be a list of dictionaries!")
    else:
        raise Exception("Error: Input data must be a list!")