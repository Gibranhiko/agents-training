from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.observability import configure_logging
from app.storage.repository import init_db
from app.api.routes import router

load_dotenv()
configure_logging()

app = FastAPI(title="AI Lead Qualification", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()


app.include_router(router)
