from fastapi import  Depends, APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder

from langgraph.types import Command
from utils.agent.graph import Graph
from utils.common.common import get_uuid_string

from config import Session, get_db, logger
from core.db.models import Chapter
from core.db.schemas import (
    AnswerSchema,
    ChapterInputRequest,
    NextTopicSchema
)
    
dialogue_routes = APIRouter()


@dialogue_routes.post("/start-dialogue")
def start_dialogue(request: ChapterInputRequest, db: Session = Depends(get_db)):
    try:
        chapter = db.query(Chapter).filter(Chapter.id == request.chapter_id).first()

        topics = [
            {
                "url": subtopic.source,
                "content": subtopic.content,
                "topic": subtopic.subtopic_name,
                "notes": subtopic.content,
                "quizzes": [],
                "state": None,
                "messages": []
            }
            for subtopic in chapter.subtopics
        ]

        graph = Graph.build_graph()
        random_id = get_uuid_string()
        config = {"configurable": {"thread_id": random_id}}
        dialogues = {"index": -1, "dialogues": topics}
        result = graph.stream(dialogues, config)

        for chunk in result:
            if "__interrupt__" in chunk:                
                graph_query = chunk["__interrupt__"][0].value
                
                return {
                    "dialogue": graph_query,
                    "session_id": random_id
                }
    except Exception as e:
            logger.error("Error occured: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error"
                )

@dialogue_routes.post("/review-response")
def review_response(request: AnswerSchema):
    try:
        session_id = request.session_id
        user_answer = request.answer
        config = {"configurable": {"thread_id": session_id}}
        graph = Graph.build_graph()

        result = graph.stream(Command(resume=user_answer), 
                            config)
        graph_query = None
        state = None

        for chunk in result:
            if "__interrupt__" in chunk:                
                
                snapshot = graph.get_state(config).values
                state_index = snapshot["index"]
                state = snapshot["dialogues"][state_index]["state"]

                if state == "clear":
                    graph_query = snapshot["dialogues"][state_index]["quizzes"] 
                    graph_query = jsonable_encoder(graph_query)
                else:
                    graph_query = chunk["__interrupt__"][0].value
                break

        if graph_query is None:
            return {
                "response": "<p><b>The dialogue ends here.</b></p>",
                "session_id": session_id,
                "state": state
            }

        return {
            "response": graph_query,
            "session_id": session_id,
            "state": state
        }
    except Exception as e:
            logger.error("Error occured: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error"
                )

@dialogue_routes.post("/next-topic")
def next_topic(request: NextTopicSchema):
    try:
        session_id = request.session_id
        config = {"configurable": {"thread_id": session_id}}
        graph = Graph.build_graph()

        result = graph.stream(Command(resume="Let's continue"), config)
        graph_query = None

        for chunk in result:
            if "__interrupt__" in chunk:
                graph_query = chunk["__interrupt__"][0].value
                break

        if graph_query is not None:
            return {
                "response": graph_query,
                "session_id": session_id
            }

        return {
        "response": "<p><b>The dialogue ends here.</b></p>",
        "session_id": session_id
        }    

    except Exception as e:
            logger.error("Error occured: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error"
            )