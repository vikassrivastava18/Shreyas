import json
from dotenv import load_dotenv

from fastapi import (APIRouter, Request,
                     Depends, HTTPException,
                    status)
from fastapi.responses import (HTMLResponse,
                               JSONResponse)
from fastapi.templating import Jinja2Templates

from config import Session, get_db, logger
from core.db.models import Book, Chapter, Subtopic
from core.db.schemas import (BookDetailFooterResponse,
                        BookDetailResponse,
                        ChapterRequest)
from core.db.query import add_new_book, get_books


# Create Route instance
book_routes = APIRouter() 

# Load environment variables
load_dotenv()

# Configure the templates path
templates = Jinja2Templates(directory="../frontend")


@book_routes.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "home_v2.html", {"request": request, "name": "FastAPI"}
    )


@book_routes.get("/books")
def books(order: str = "asc", db: Session = Depends(get_db)):
    """Get books sorted by name asc/desc based on query param."""
    try:        
        books = get_books()
        return [{
            "id": book.id, 
            "name": book.book_name
            } for book in books]
    except Exception as e:
        logger.error("Error in Fetching books: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error fetching sorted book list {e}"
            )


@book_routes.get("/books/{book_id}/footer", response_model=BookDetailFooterResponse)
def get_book_footer(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book


@book_routes.post("/chapter-subtopics/", response_model=BookDetailResponse)
async def chapter_subtopics_list(request: ChapterRequest,
                                 db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == request.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book


@book_routes.post("/add-book-new")
def add_book(file_path: str):
    try:
        # Open the file and load its content into a Python dictionary
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        new_book = add_new_book(name=data["bookName"], file_name='...', 
                                logo_path='....',
                                chapters=data["chapters"]
                                )
        return JSONResponse(status_code=status.HTTP_201_CREATED, 
                        content={"message": "Book added successfully"})

    except Exception as e:
        logger.error("Error in Adding new book: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e))
