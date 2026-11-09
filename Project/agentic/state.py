from typing import Any, Dict, List, TypedDict
class ClearanceState(TypedDict, total=False):
    campaign_reference: str
    assessment_id: str
    run_id: str
    user: str
    submissions: List[dict]
    spots: List[dict]
    notes: List[dict]
    analyses: Dict[str, Any]
    decision: str
    result: Dict[str, Any]
    status: str
    error: str

# Public contract name used by workflow callers.
ClearanceAssessmentState = ClearanceState