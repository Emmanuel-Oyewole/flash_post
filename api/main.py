from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config.settings import settings
from api.config.database import sessionmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager to initialize the database.
    """
    yield
    if sessionmanager._engine is not None:
        await sessionmanager.close()


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
