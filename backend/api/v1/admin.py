import os, re, shutil, time
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader

from fastapi import (UploadFile,File, HTTPException,
                     APIRouter, Request, Form,
                     status, Depends)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from backend.core.llm.generate import process_llm_response
from utils.common.common import extract_text_from_pdf
from backend.core.config import logger, Session, get_db
from backend.core.db.models import Book
from backend.core.db.schemas import BookResponse
from backend.core.db.query import bulk_insert_chapters
from backend.core.llm.vector import store_vector_store

admin_routes = APIRouter() 
load_dotenv()

# Configure the template
templates = Jinja2Templates(directory="frontend")


def verify_login():
    """Dependency to verify login status"""
    from api.v1.auth import logged_in
    if not logged_in:
        logger.warning("Unauthorized access attempt - user not logged in")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login?error=not_logged_in"}
        )


@admin_routes.get("/", response_class=HTMLResponse)
async def admin_page(request: Request, _ = Depends(verify_login)):
    return templates.TemplateResponse("adminPage.html", {"request": request})


@admin_routes.get("/admin-books")  
def get_admin_books(db: Session = Depends(get_db)):
    """Retrieve all books with their IDs and names."""
    try:
        books = db.query(Book).options(joinedload(Book.chapters)).all()
        response = [
            {
                "id": book.id,
                "name": book.book_name, 
                "logo1": book.logo1,
                "logo2": book.logo2,
                "status": book.status,
                "disclaimer": book.disclaimer,
                "chaptersTopics": [chapter.chapter_name for chapter in book.chapters],
            } for book in books] 
        return response
    except Exception as e:
        logger.error(f"Error retrieving books: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve book list")
    

# Upload API
@admin_routes.post("/upload-book/", response_model=BookResponse)
def upload_book(
    book_name: str = Form(...),
    book_file: UploadFile = File(...),
    logo1: UploadFile = File(None),
    logo2: Optional[UploadFile] = File(None),
    disclaimer: str = Form(...),
    db: Session = Depends(get_db)
    ):
    # First check if book already exists
    existing_book = db.query(Book).filter(Book.book_name.ilike(book_name)).first()
    # breakpoint()
    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,         
            detail="A book with this name already exists"
        )

    # Process disclaimer first (no file operations yet)
    current_year = datetime.now().year
    updated_disclaimer = re.sub(
        r'Copyright © \d{4}',
        f'Copyright © {current_year}',
        disclaimer
    )

    # Extract text and process chapters before any file operations
    try:
        # Save the book file temporarily to process it
        temp_book_path = f"temp_{book_file.filename}"
        with open(temp_book_path, "wb") as f:
            shutil.copyfileobj(book_file.file, f)
        pdf_text = extract_text_from_pdf(temp_book_path,'')
        book_data = process_llm_response(pdf_text=pdf_text)
        
        # Validate chapters exist before proceeding
        if not book_data.get("chapters"):
            os.remove(temp_book_path)  # Clean up temp file
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chapters found in the book"
            )
            
    except Exception as e:
        if os.path.exists(temp_book_path):
            os.remove(temp_book_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing book content: {str(e)}"
        )

    # Now proceed with permanent file storage and DB operations
    try:
        book_path = f"folders/books/{book_file.filename}"
        os.rename(temp_book_path, book_path)  # Move from temp to permanent location

        logo1_path = None
        if logo1:
            logo1_path = f"folders/logos/{logo1.filename}"
            with open(logo1_path, "wb") as f:
                shutil.copyfileobj(logo1.file, f)

        logo2_path = None
        if logo2:
            logo2_path = f"folders/logos/{logo2.filename}"
            with open(logo2_path, "wb") as f:
                shutil.copyfileobj(logo2.file, f)

        # Create and save the book
        new_book = Book(
            book_name=book_name,
            book_file=book_path,
            logo1=logo1_path,
            logo2=logo2_path,
            disclaimer=updated_disclaimer
        )
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        
        # Save chapters
        bulk_insert_chapters(book_data["chapters"], new_book.id, db=db)
        
        # Create vector store
        loader = PyPDFLoader(book_path)
        store_vector_store(loader.load())
        
        return new_book
        
    except Exception as e:
        # Clean up any files that might have been created
        if os.path.exists(book_path):
            os.remove(book_path)
        if logo1_path and os.path.exists(logo1_path):
            os.remove(logo1_path)
        if logo2_path and os.path.exists(logo2_path):
            os.remove(logo2_path)
            
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving book: {str(e)}"
        )
    

@admin_routes.post("/extract-chapters/")
async def extract_chapters(file: UploadFile = File(...)):
    start_time = time.time()
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    temp_pdf = f"temp_{file.filename}"
    try:
        
        with open(temp_pdf, "wb") as buffer:
            buffer.write(file.file.read())
        
        text = extract_text_from_pdf(temp_pdf)
        result = get_chapters_from_llm(text)
        
        elapsed_time = time.time() - start_time
        print(f"Processing completed in {elapsed_time:.2f} seconds")
        print('response-----', result)
        return JSONResponse(content=result)
    
    finally:
        if os.path.exists(temp_pdf):
            # os.remove(temp_pdf)
            pass

