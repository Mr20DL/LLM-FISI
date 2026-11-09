from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.llm_service import answer_question, LLMServiceError

router = APIRouter(tags=["Assistant"])


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1500,
        description="Pregunta del estudiante o docente.",
    )


class QueryResponse(BaseModel):
    answer: str
    model: str
    source: str


@router.post("/assistant/query", response_model=QueryResponse)
def query_assistant(payload: QueryRequest):
    try:
        answer = answer_question(payload.question)
        return QueryResponse(
            answer=answer,
            model="fisi-assistant:qwen3-4b",
            source="base_conocimiento_fisi",
        )
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
