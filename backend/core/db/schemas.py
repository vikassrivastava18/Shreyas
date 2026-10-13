from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# --- Common Question Types ---
class QuestionType(str, Enum):
    """Enumeration of all supported question types."""
    mcq = "MCQs"
    true_false = "True/False"
    matching = "Matching"
    short_question_answer = "Short Question Answer"
    essay = "Essay Questions"


class SubtopicCreate(BaseModel):
    subtopic_name: str


class ChapterCreate(BaseModel):
    chapter_name: str
    subtopics: List[str]
    

class BookResponse(BaseModel):
    id: int
    book_name: str
    book_file: str
    logo1: Optional[str]
    logo2: Optional[str]
    status: bool
    disclaimer: str

    class Config:
        orm_mode = True


class ChapterResponse(BaseModel):
    id: int
    chapter_name: str
    subtopics: List[str]

    class Config:
        orm_mode = True


class ChapterRequest(BaseModel):
    book_id: int


class ChapterInputRequest(BaseModel):
    chapter_id: int

# Response
class SubtopicOut(BaseModel):
    subtopic_name: str
    id: int

    class Config:
        orm_mode = True


class ChapterOut(BaseModel):
    chapter_name: str
    id: int
    subtopics: List[SubtopicOut] = []

    class Config:
        orm_mode = True


class BookDetailResponse(BaseModel):
    id: int
    notebook_name: str = Field(..., alias="book_name")
    chapters: List[ChapterOut] = []

    class Config:
        orm_mode = True
    

class BookDetailFooterResponse(BaseModel):
    id: int
    notebook_name: str = Field(..., alias="book_name")
    # chapters: List[ChapterOut] = []
    logo1: Optional[str]= None
    logo2: Optional[str]= None
    disclaimer:Optional[str]= None

    class Config:
        orm_mode = True


class CaseStudyRequest(BaseModel):
    """Request model for generating a case study with customizable question types."""
    topics: List[str]
    chapters: List[str]
    notes: str = None 
    number_of_question:Optional[int]= None
    question_types: List[QuestionType]
    language: str
    textbook_name: str
    selections: List


class PPTGenerationRequest(BaseModel):
    """Request model for generating a PowerPoint based on selected topics."""
    book_id: int
    topics: List[str]
    textbook_name: str
    language: Optional[str] = None
    notes: Optional[str] = None
    selections: List


class QuizRequest(BaseModel):
    """Request model for generating a quiz based on selected topics and question types."""

    topics: List[str] 
    question_types: List[QuestionType]
    notes: str = None 
    language: str
    number_of_question:Optional[int]= None
    textbook_name: str
    selections: List


class SummarizeRequest(BaseModel):
    """Request model for summarizing selected topics in a specified language."""

    topics: List[str]
    language: str
    notes: Optional[str] = None
    textbook_name: str
    selections: List


class PPTPreviewRequest(BaseModel):

    """Request model for generating a PowerPoint based on selected topics."""
    topics: List[str]
    textbook_name: str
    language: Optional[str] = None
    notes: Optional[str] = None
    textbook_name: str
    selections: List


class WorksheetRequestCompatible(BaseModel):
    """Request model for generating a worksheet with selected question types."""

    topics: List[str]
    question_types: List[QuestionType]
    number_of_question: Optional[int] = None
    language: str
    notes: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None
    textbook_name: str
    selections: List


class SubchapterRequest(BaseModel):
    """Schema for subchapter"""
    url: str
    content: str

class ChapterContentRequest(BaseModel):
    """Request model for generating quizzes using chapter content"""
    subchapters: List[SubchapterRequest]


class MCQ(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str
    url: str


class TrueFalse(BaseModel):
    question: str
    answer: bool
    explanation: str
    url: str


class FillBlank(BaseModel):
    question: str
    answer: str
    url: str


class QuizResponse(BaseModel):
    mcq: List[MCQ]
    true_false: List[TrueFalse]
    fill_blank: List[FillBlank]


class UserQuery(BaseModel):
    query: str


class Question(BaseModel):
    topic: str
    question: str
    answer: str
    source: str


class QuestionsSchema(BaseModel):
    questions: List[Question]


class AnswerSchema(BaseModel):
    session_id: str
    answer: str
    

class DialogueResponse(BaseModel):
    questions: List[Question]
    index: int
    session_id: str
    user_answer: str
    hint_taken: bool
    llm_response: str
    chapter: str



class QueryResponse(BaseModel):
    correct: bool
    comment: str


class NextTopicSchema(BaseModel):
    session_id: str

