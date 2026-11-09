from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
class SignInRequest(BaseModel):
    username: str
    password: str
class UserResponse(BaseModel):
    username: str; display_name: str; role: str
class AssessmentRequest(BaseModel):
    campaign_reference: str
    executive_request: str = Field("", min_length=5)
class DecisionRequest(BaseModel):
    decision: str
    reason: str = Field("", min_length=10)
    decision_reason: Optional[str] = None
class AssessmentResponse(BaseModel):
    assessment_id: str; campaign_reference: str; status: str; result: Optional[Dict[str,Any]]=None
    class Config:
        orm_mode = True