from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup — good place to verify DB connection
    yield
    # Runs on shutdown

app = FastAPI(title="Job Tracker API", version="0.1.0", lifespan=lifespan)