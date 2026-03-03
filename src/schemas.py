from pydantic import BaseModel, Field
from typing import List, Optional

class Citation(BaseModel):
    doc_id: str
    section: str
    timestamp: str

class CopilotResponse(BaseModel):
    final_response: str
    citations: List[Citation]
    confidence_level: str = Field(description="High, Medium, or Low")
    confidence_reason: str
    escalation_recommendation: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None