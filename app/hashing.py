import os
import bcrypt
import base64


def generate_salt() -> str:
    salt = os.urandom(32)
    return base64.b64encode(salt).decode('utf-8')

def get_password_hash(password: str, salt: str) -> str:
    salted_password = password + salt
    hashed = bcrypt.hashpw(
        salted_password.encode('utf-8'),
        bcrypt.gensalt()
    )
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    salted_password = plain_password + salt
    return bcrypt.checkpw(
        salted_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )