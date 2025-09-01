from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.database import sessionmanager
from .config.redis_db import redis_manager
from .user import router as user_router
from .authentication import router as auth_router
from .blogs import router as blog_router
from .comment import router as comment_router
from .like import router as like_router
from .tag import router as tag_router
from .models import User  # noqa
from .models import Blog  # noqa
from .models import Comment  # noqa
from .models import Like  # noqa
from .models import Tag, blog_tags  # noqa


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
