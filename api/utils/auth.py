from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"])
def hash_password(password: str) -> str:
    """
    Converts plain password to hashed value

    Args:
        password(str): Password to be hashed

    Returns:
        hashed-value(str): The hashed value of the input password
    """
    return pwd_context.hash(password)
