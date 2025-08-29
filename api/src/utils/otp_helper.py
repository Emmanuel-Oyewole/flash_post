import hashlib
from ..config.settings import settings


def hash_otp_code(code: str) -> str:
    """Hashes the OTP code."""
    # Use a secure, fast hashing algorithm. Add a secret key for salt.
    return hashlib.sha256((code + settings.otp_secret).encode()).hexdigest()


def verify_otp_code(code: str, hashed_code: str) -> bool:
    """Verifies a plain-text OTP against a hashed OTP."""
    return hash_otp_code(code) == hashed_code
