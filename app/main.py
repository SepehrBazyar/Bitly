from fastapi import FastAPI

from app.middleware import logging_middleware
from app.routers import urls

app = FastAPI()


app.middleware("http")(logging_middleware)
app.include_router(urls.router)
