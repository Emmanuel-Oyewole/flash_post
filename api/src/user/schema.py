import enum
from uuid import UUID
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, AfterValidator
from ..shared.schema import PublicUser
from ..config.settings import settings
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


# Password policy
SPECIAL_CHARS: set[str] = {
    "$",
    "@",
    "#",
    "%",
    "!",
    "^",
    "&",
    "*",
    "(",
    ")",
    "-",
    "_",
    "+",
    "=",
    "{",
    "}",
    "[",
    "]",
}


MIN_LENGTH = settings.min_length
MAX_LENGTH = settings.max_length
INCLUDES_SPECIAL_CHARS = settings.includes_special_chars
INCLUDES_NUMBERS = settings.includes_numbers
INCLUDES_LOWERCASE = settings.includes_lowercase
INCLUDES_UPPERCASE = settings.includes_uppercase


def validate_password(v: str) -> str:
    min_length = MIN_LENGTH
    max_length = MAX_LENGTH
    includes_special_chars = INCLUDES_SPECIAL_CHARS
    includes_numbers = INCLUDES_NUMBERS
    includes_lowercase = INCLUDES_LOWERCASE
    includes_uppercase = INCLUDES_UPPERCASE
    special_chars = SPECIAL_CHARS

    if len(v) < min_length or len(v) > max_length:
        raise ValueError(
            f"length should be at least {min_length} but not more than {max_length}"
        )

    if includes_numbers and not any(char.isdigit() for char in v):
        raise ValueError("Password should have at least one numeral")

    if includes_uppercase and not any(char.isupper() for char in v):
        raise ValueError("Password should have at least one uppercase letter")

    if includes_lowercase and not any(char.islower() for char in v):
        raise ValueError("Password should have at least one lowercase letter")

    if includes_special_chars and not any(char in special_chars for char in v):
        raise ValueError(
            f"Password should have at least one of the symbols {special_chars}"
        )

    return v


ValidatePassword = Annotated[str, AfterValidator(validate_password)]


class UserBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    bio: str | None = None
    avatar: str | None = None


class UpdateUser(UserBase):
    pass


class GetUser(PublicUser):
    pass


class CreateUser(BaseModel):
    email: EmailStr = Field(...)
    password: str= Field(...)
    role: UserRole = Field(default=UserRole.USER)


class PublicUserResp(BaseModel):
    id: UUID
    user_info: PublicUser
