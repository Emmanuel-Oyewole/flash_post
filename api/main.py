from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config.database import sessionmanager
from api.config.redis_db import redis_manager
from api.user import router as user_router
from api.authentication import router as auth_router
from api.blogs import router as blog_router
from api.comment import router as comment_router
from api.like import router as like_router
from api.tag import router as tag_router
from api.user.model import User  # noqa
from api.blogs.model import Blog  # noqa
from api.comment.model import Comment  # noqa
from api.like.model import Like  # noqa
from api.tag.model import Tag  # noqa


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager to initialize the database.
    """
    await redis_manager.connect()
    yield
    if sessionmanager._engine is not None:
        await sessionmanager.close()
    await redis_manager.close()


app = FastAPI(title="Flash Blog API", version="0.0.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Flash Blog API!"}


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(blog_router)
app.include_router(comment_router)
app.include_router(like_router)
app.include_router(tag_router)
