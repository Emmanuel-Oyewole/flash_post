

class AuthService:
    def __init__(self):
        self._secret_key = "your-secret-key"
        self._algorithm = "HS256"
        self._access_token_expire_minutes = 30

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

    def create_access_token(self, subject: dict) -> str:
        pass
