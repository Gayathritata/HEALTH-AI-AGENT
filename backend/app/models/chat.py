from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    user_message: str
    ai_response: str
    response_type: str
    severity: str = "low"
    emergency: bool = False
    current_symptom: str | None = None


class ChatHistoryItem(BaseModel):
    user_message: str
    ai_response: str
    response_type: str
    severity: str = "low"
    emergency: bool = False
    current_symptom: str | None = None
    created_at: str | None = None

