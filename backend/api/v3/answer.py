import uuid
from fastapi import Depends, HTTPException, status
from fastapi import APIRouter
from langgraph.types import Command

from config import Session, get_db, logger
from core.db.models import Chapter
from core.db.schemas import AnswerSchema, ChapterInputRequest

from utils.agent.graph import AnswerGraph


answer_routes = APIRouter()


@answer_routes.post("/start-dialogue")
def start_dialogue(request: ChapterInputRequest, db: Session = Depends(get_db)):
    try:
        chapter = db.query(Chapter).filter(Chapter.id == request.chapter_id).first()

        topics = [
            {"notes": subtopic.content, 
             "topic": subtopic.subtopic_name,
            }
            for subtopic in chapter.subtopics
        ]
        graph = AnswerGraph.build_graph()
        random_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": random_id}}
        dialogues = {"topics": topics, 
                     "topic": {}, 
                     "index": -1,
                     "max_ind": len(topics)}
        result = graph.stream(dialogues, config)

        for chunk in result:
            if "__interrupt__" in chunk:
                question = chunk["__interrupt__"][0].value

                return {
                        "question": question,
                        "session_id": random_id
                        }
    except AttributeError as e:
        logger.error("Error in Fetching books: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Chapter not found"
            )

    except Exception as e:
        logger.error("Error occured: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Internal server error"
            )


@answer_routes.post("/evaluate-response")
def review_response(request: AnswerSchema):
    answer, session_id = request.answer, request.session_id
    graph = AnswerGraph.build_graph()
    config = {"configurable": {"thread_id": session_id}}

    result = graph.stream(Command(resume=answer), config)

    for chunk in result:
        if "__interrupt__" in chunk:
            response = chunk["__interrupt__"][0].value
            snapshot = graph.get_state(config).values
            assessment = snapshot["topic"]["assessment"]
            return {
                "response": response,
                "session_id": session_id,
                "complete": False,
                "assessment": assessment
            }

    return {
        "response": "Session completed!",
        "session_id": session_id,
        "complete": True,
    }
