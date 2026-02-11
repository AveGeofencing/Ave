import string
from pynanoid import generate
from argon2 import PasswordHasher

ph: PasswordHasher = PasswordHasher()

def generate_id(size: int = 10):
    alphabet = string.ascii_letters + string.digits
    return generate(alphabet=alphabet, size=size)

def hash_password(password: str) -> str:
    return ph.hash(password)