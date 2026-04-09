from typing import List
import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.chat import ChatHistoryItem, ChatRequest, ChatResponse
from app.services.agent import run_health_agent
from app.services.supabase_client import get_chat_history, save_chat_history, validate_access_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        access_token = authorization.split(" ", 1)[1]
        user_id = validate_access_token(access_token)

        # Get recent chat history to determine conversation context
        recent_history = get_chat_history(user_id)[-20:]  # Last 20 messages
        
        agent_result = run_health_agent(payload.message, recent_history)
        ai_response = agent_result["ai_response"]
        response_type = agent_result["response_type"]
        severity = agent_result.get("severity", "low")
        emergency = agent_result.get("emergency", False)
        current_symptom = agent_result.get("current_symptom")

        save_chat_history(
            user_id=user_id,
            user_message=payload.message,
            ai_response=ai_response,
            response_type=response_type,
            severity=severity,
            emergency=emergency,
            current_symptom=current_symptom,
        )

        return ChatResponse(
            user_message=payload.message,
            ai_response=ai_response,
            response_type=response_type,
            severity=severity,
            emergency=emergency,
            current_symptom=current_symptom,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Chat error: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {exc}") from exc


@router.get("/chat/history", response_model=List[ChatHistoryItem])
def chat_history(authorization: str | None = Header(default=None)) -> List[ChatHistoryItem]:
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        access_token = authorization.split(" ", 1)[1]
        user_id = validate_access_token(access_token)
        rows = get_chat_history(user_id)
        return [ChatHistoryItem(**row) for row in rows]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load chat history: {exc}") from exc
