import json
from fastapi import (APIRouter, 
                     Depends, 
                     HTTPException, 
                     status)
from fastapi.responses import (JSONResponse)

from core.db.query import get_books
from core.db.models import Book
from core.db.schemas import (BookDetailResponse,
                        ChapterRequest)
from core.db.query import add_new_book, get_books
from config import Session, get_db, logger


book_routes = APIRouter()

@book_routes.get("/books")
def books():
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
