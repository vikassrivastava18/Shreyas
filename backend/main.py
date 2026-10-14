from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import engine, Base
from api.v3.dialogue import dialogue_routes
from api.v3.ask import ask_routes
from api.v3.answer import answer_routes

Base.metadata.create_all(bind=engine)

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Include the home routers (loaded immediately)
from api.v1.books import book_routes
app.include_router(
    book_routes,
    tags=["Books"]
)

app.include_router(
    ask_routes,
    prefix="/ask",
    tags=["Ask"]
)

app.include_router(
    dialogue_routes,
    prefix="/dialogue",
    tags=["Dialogue"]
)

app.include_router(
        answer_routes,
        prefix="/answer",
        tags=["Answer"]
    )
