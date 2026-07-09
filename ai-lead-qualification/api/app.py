from dotenv import load_dotenv
from fastapi import FastAPI

from observability import configure_logging
from storage import init_db
from api.routes import router

load_dotenv()
configure_logging()

app = FastAPI(title="AI Lead Qualification", version="1.0.0")

@app.on_event("startup")
def startup():
    init_db()

app.include_router(router)
