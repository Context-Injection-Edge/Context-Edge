"""
Recommendations API
Endpoints for ML recommendation approval workflow
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

# Initialize service
recommendation_service = RecommendationService()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ApprovalRequest(BaseModel):
    """Request to approve recommendation"""
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    """Request to reject recommendation"""
    reason: str


class RecommendationResponse(BaseModel):
    """Recommendation details"""
    recommendation_id: str
    device_id: str
    action_type: str
    target_parameter: str
    current_value: Optional[float]
    recommended_value: float
    unit: str
    reasoning: str
    confidence: float
    priority: int
    status: str
    is_within_limits: bool
    min_safe_value: Optional[float]
    max_safe_value: Optional[float]
    age_minutes: Optional[float]
    created_at: datetime
    expires_at: Optional[datetime]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/pending", response_model=List[RecommendationResponse])
async def get_pending_recommendations(
    device_id: Optional[str] = None
):
    """
    Get all pending recommendations awaiting operator approval

    Query Parameters:
        device_id: Optional filter by device ID

    Returns:
        List of pending recommendations sorted by priority
    """
    recommendations = await recommendation_service.get_pending_recommendations(device_id)
    return recommendations


@router.post("/{rec_id}/approve")
async def approve_recommendation(
    rec_id: str,
    approval: ApprovalRequest,
    x_operator_id: Optional[str] = Header(None, alias="X-Operator-ID")
):
    """
    Approve ML recommendation (Safety Gate 1)

    Path Parameters:
        rec_id: Recommendation ID

    Headers:
        X-Operator-ID: Operator username/ID (for audit trail)

    Request Body:
        notes: Optional operator notes

    Returns:
        Approval result

    Safety Gates Applied:
    1. ✅ Operator approval (this endpoint)
    2. ✅ Range validation (automatic)
    3. ⏳ PLC validation (happens during execution)
    """
    operator = x_operator_id or "unknown"

    result = await recommendation_service.approve_recommendation(
        rec_id=rec_id,
        operator=operator,
        notes=approval.notes
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/{rec_id}/reject")
async def reject_recommendation(
    rec_id: str,
    rejection: RejectionRequest,
    x_operator_id: Optional[str] = Header(None, alias="X-Operator-ID")
):
    """
    Reject ML recommendation

    Path Parameters:
        rec_id: Recommendation ID

    Headers:
        X-Operator-ID: Operator username/ID (for audit trail)

    Request Body:
        reason: Reason for rejection (required for audit)

    Returns:
        Rejection result
    """
    operator = x_operator_id or "unknown"

    result = await recommendation_service.reject_recommendation(
        rec_id=rec_id,
        operator=operator,
        reason=rejection.reason
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/{rec_id}")
async def get_recommendation(rec_id: str):
    """
    Get recommendation details by ID

    Path Parameters:
        rec_id: Recommendation ID

    Returns:
        Recommendation details
    """
    # TODO: Implement get_recommendation_by_id in service
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/history")
async def get_recommendation_history(
    device_id: Optional[str] = None,
    limit: int = 100
):
    """
    Get recommendation history

    Query Parameters:
        device_id: Optional filter by device
        limit: Maximum number of records (default 100)

    Returns:
        List of historical recommendations with execution status
    """
    # TODO: Implement get_history in service
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/expire")
async def expire_old_recommendations():
    """
    Manually trigger expiration of old recommendations

    This endpoint is typically called by a cron job or scheduler.
    Recommendations expire after configured timeout (default 10 minutes).

    Returns:
        Number of recommendations expired
    """
    expired_count = await recommendation_service.expire_old_recommendations()
    return {"expired_count": expired_count}
