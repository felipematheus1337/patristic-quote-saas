from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.st_controller import router

app = FastAPI(title="Patristic Quotes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
