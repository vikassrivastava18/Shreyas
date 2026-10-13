topics = [
    {
        "topic": "Small Business Defined",
        "notes": f"""Small businesses are often the starting point for entrepreneurs as they develop their ideas and build a customer base. 
        The Small Business Administration (SBA) defines a small business as a for-profit entity with fewer than 500 employees. This definition makes
        these businesses eligible for various government programs and preferences. Small businesses play a crucial role in our economy and communities.""",
        "quizzes": [],
        "messages": [],
    },
    {
        "topic": "Small Business Impact",
        "notes": f"""There are over 33.2 million small businesses in the United States, making up 99.9% of all firms. From 1995 to 2021, small businesses created 
        17.3 million net new jobs, significantly more than large businesses. Despite challenges like the COVID-19 recession, small businesses rebounded quickly,
        demonstrating their resilience and importance to economic recovery. They contribute to local economies by reinvesting paychecks and taxes, supporting 
        new businesses, and improving
        public services. On average, small businesses offer competitive wages, averaging $30.42 per hour, translating to an annual income of $63,000.""",
        "quizzes": [],
        "messages": [],
    },
    {
        "topic": "Small Business Demographics",
        "notes": f"""43.4% of small businesses are owned by females, reflecting progress toward gender equality in entrepreneurship.
        20.4% are owned by racial minorities, including 14.5% by Hispanics.
        6.1% are owned by veterans, contributing diverse perspectives to the U.S. economy.
        Hispanic-owned businesses, for example, pay over $100 billion annually in payroll to their 1 million workers.""",
        "quizzes": [],
        "messages": [],
    },
]

from pydantic import BaseModel

class MCQ(BaseModel):
    question: str
    options: list[str]
    answer: str
    explanation: str

class TrueFalse(BaseModel):
    question: str
    answer: bool
    explanation: str

class QuizSchema(BaseModel):
    mcq: list[MCQ]
    true_false: list[TrueFalse]


from typing import TypedDict

class ConceptState(TypedDict):
    topic: str
    notes: str
    quizzes: list[QuizSchema]
    messages: list

class DialogueState(TypedDict):
    index: int
    dialogues: list[ConceptState]

class NextTopicSchema(TypedDict):
    session_id: str
