from sqlalchemy import (Column, Integer,
                        String, Boolean,
                        ForeignKey, JSON)
from sqlalchemy.orm import relationship
from config import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String, nullable=False, unique=True)
    book_file = Column(String, nullable=False)
    logo1 = Column(String, nullable=True)
    logo2 = Column(String, nullable=True)
    status = Column(Boolean, default=True)
    disclaimer = Column(String, nullable=True)
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_name = Column(String, nullable=False)
    book = relationship("Book", back_populates="chapters")
    subtopics = relationship("Subtopic", back_populates="chapter", cascade="all, delete")


class Subtopic(Base):
    __tablename__ = "subtopics"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    subtopic_name = Column(String, nullable=False)
    content = Column(String)
    chapter = relationship("Chapter", back_populates="subtopics")
    source = Column(String)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)


class Dialogue(Base):
    __tablename__ = "dialogues"
    session_id = Column(String, primary_key=True, index=True)
    dialogue = Column(JSON, nullable=True)


