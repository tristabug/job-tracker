from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import auth, applications, contacts


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Job Tracker API", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(contacts.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
