import factory
from ...src.models.user_model import User
from ...src.utils.auth import hash_password as get_password_hash

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    id = factory.Faker("uuid4")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    middle_name = factory.Faker("first_name")
    bio = factory.Faker("text")
    avatar = factory.Faker("image_url")
    email_verified = factory.Faker("boolean", chance_of_getting_true=75)
    is_active = factory.Faker("boolean", chance_of_getting_true=90)
    hashed_password = factory.LazyFunction(
        lambda: get_password_hash("defaultpassword")
    )
    role = factory.Iterator(["admin", "user"])

    @classmethod
    def create(cls, model_class, *args, **kwargs):
        # Handle the password argument before creating the user
        if "password" in kwargs:
            kwargs["hashed_password"] = get_password_hash(kwargs.pop("password"))
        return super()._create(model_class, *args, **kwargs)
