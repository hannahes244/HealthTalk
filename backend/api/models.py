from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class UserChatRequest(BaseModel):
    message: str = Field(..., description="The user's message.")
    session_id: str = Field(..., description="A unique ID for the chat session.")

class AssistantChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's response to the user's message.")
    # Returns the latest response.

class SessionClearRequest(BaseModel):
    session_id: str = Field(..., description="The ID of the session to clear.")

class SessionClearResponse(BaseModel):
    message: str = Field(..., description="Confirmation message.")