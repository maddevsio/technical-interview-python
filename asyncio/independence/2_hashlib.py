import hashlib
import os
import random
import string

# Мы узнали что в базе хранятся незахешированные пароли. И нам нужно срочно захешировать их все.
# Пользователей в базе очень много. Даже с нашими мощностями это будет крайне долгая операция.
# Задача:
# Как нам ускорить следующий код?
def random_password(length: int) -> bytes:
    """Generate random password with given length."""
    ascii_lowercase = string.ascii_lowercase.encode()
    return b''.join(bytes(random.choice(ascii_lowercase)) for _ in range(length))

# База данных с открытыми паролями
passwords = [random_password(10) for _ in range(100_000_000_000)]


def get_hash(password: bytes) -> str:
    """Get the password hash."""
    salt = os.urandom(16)
    return str(hashlib.scrypt(password, salt=salt, n=2048, p=1, r=8))


def hash_all_passwords() -> list[str]:
    """Hash all the passwords."""
    hashed_passwords = []

    for password in passwords:
        hashed_password = get_hash(password)
        hashed_passwords.append(hashed_password)

    return hashed_passwords
