from typing import List

from config import Session, logger
from utils.common.common import verify_password
from core.db.schemas import ChapterCreate
from .models import Book, Chapter, Subtopic, User


async def get_content(selections: List[dict]):
    db = Session()
    try:
        result = []
        for selection in selections:
            # Fetch the first matching chapter
            chapter = db.query(Chapter).filter(Chapter.chapter_name == selection["chapter"]).first()
            # Ensure chapter exists (to avoid NoneType errors)
            if chapter:
                # Use the chapter_id in the Subtopic query
                subtopics = db.query(Subtopic).filter(Subtopic.chapter_id == chapter.id).all()
                result.extend(subtopics)
        data = [subtopic.content for subtopic in result]
        data = "\n\n".join(data)
        return data
    finally:
        db.close()


def bulk_insert_chapters(data: List[ChapterCreate], book_id: int, db: Session):
    for chapter_data in data:
        # print("Raw chapter data:", chapter_data)  
        if not isinstance(chapter_data, dict):
            logger.error(f"Invalid chapter data format: {type(chapter_data)}")
            continue
            
        try:
            chapter = Chapter(
                chapter_name=chapter_data.get('chapter_title'),
                book_id=book_id
            )
            db.add(chapter)
            db.flush()

            subtopics = chapter_data.get("subtopics", [])
            if not isinstance(subtopics, list):
                logger.error(f"Invalid subtopics format: {type(subtopics)}")
                continue
                
            for subtopic_title in subtopics:
                sub = Subtopic(subtopic_name=subtopic_title, chapter_id=chapter.id)
                db.add(sub)
                
        except Exception as ex:
            logger.error(f"Error processing chapter: {ex}", exc_info=True)
            db.rollback()
            raise  # Re-raise after logging
    
    try:
        db.commit()
    except Exception as error:
        logger.error(f"Commit error: {error}", exc_info=True)
        db.rollback()
        raise


def authenticate_user(username, password):
    db = Session()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return None

        # Verify password
        if verify_password(password, user.password):
            return user
    finally:
        db.close()


def get_chapter_content(chapter_id: int):
    db = Session()
    try:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        content = []

        for subtopic in chapter.subtopics:
            content.append({"url": subtopic.source, "content": subtopic.content})

        return content
    finally:
        db.close()


def get_books():
    db = Session()
    try:
        books = db.query(Book).filter(
                Book.book_name.isnot(None),
                Book.book_name != "",
                Book.status == True
            ).all()
        return books
    finally:
        db.close()


def add_new_book(name, file_name, logo_path, chapters):
    db = Session()
    try:
        new_book = Book(book_name=name, book_file=file_name, 
                        logo1=logo_path)
        db.add(new_book) # Add record to session
        db.commit() # Commit transaction
        db.refresh(new_book) 

        # Add chapters and subtopics
        for chapter in chapters:
            new_chapter = Chapter(book_id=new_book.id, chapter_name=chapter["name"])
            db.add(new_chapter)
            db.commit()
            db.refresh(new_chapter)

            # Store subchapters
            for subchapter in chapter["subchapters"]:
                sub_name = subchapter["name"]
                new_sub = Subtopic(chapter_id=new_chapter.id,
                                subtopic_name=sub_name,
                                content=subchapter["content"][:4000])
                db.add(new_sub)
                db.commit()
                db.refresh(new_sub)
        
        return {
            "id": new_book.id,
            "book_name": new_book.book_name
        }
    finally:
        db.close()