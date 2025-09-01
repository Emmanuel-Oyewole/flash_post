import factory
from ...src.models.blog_model import Blog
from .user import UserFactory


class BlogFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Blog
        sqlalchemy_session_persistence = "flush"

    id = factory.Faker("uuid4")
    title = factory.Faker("sentence", nb_words=4)
    content = factory.Faker("text", max_nb_chars=2000)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))
    author = factory.SubFactory(UserFactory)
    view_count = factory.Faker("random_int", min=0, max=1000)
    like_count = factory.Faker("random_int", min=0, max=100)
    comment_count = factory.Faker("random_int", min=0, max=50)
    is_published = factory.Faker("boolean", chance_of_getting_true=80)
    published_at = factory.Maybe(
        "is_published",
        yes_declaration=factory.Faker("date_time_this_year"),
        no_declaration=None,
    )
