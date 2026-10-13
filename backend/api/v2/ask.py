from fastapi import APIRouter, HTTPException, status

from core.db.schemas import UserQuery
from config import logger
from utils.llm.generate import answer_query_util

ask_routes = APIRouter()


@ask_routes.post("/ask-query")
def ask_query(request: UserQuery):
    try:
        docs = answer_query_util(request.query)
        return docs
    except Exception as e:
        logger.error("Some error occured: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error."
        )