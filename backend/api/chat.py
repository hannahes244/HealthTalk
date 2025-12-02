# api/chat.py
from fastapi import APIRouter, HTTPException, status
from api.models import UserChatRequest, AssistantChatResponse, SessionClearRequest, SessionClearResponse
from core.logic import process_user_message #, clear_user_session # Import core logic

router = APIRouter()

@router.post("/chat", response_model=AssistantChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_assistant(request: UserChatRequest):
    """
    Handles conversational requests with the medical assistant.
    """
    session_id = request.session_id
    user_message = request.message

    # Call the core logic that manages the conversation state
    assistant_response_text = process_user_message(session_id, user_message)

    return AssistantChatResponse(response=assistant_response_text)

@router.post("/chat/init_session", response_model=AssistantChatResponse, status_code=status.HTTP_200_OK)
async def init_chat_session(request: SessionClearRequest): # Re-using SessionClearRequest for just session_id
    """
    Initializes a new chat session and returns the first greeting.
    """
    session_id = request.session_id
    # Call process_user_message_logic with an empty message to trigger initial greeting
    initial_response = process_user_message(session_id, "")
    return AssistantChatResponse(response=initial_response)