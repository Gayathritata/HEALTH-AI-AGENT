import logging
from fastapi import APIRouter, Header, HTTPException

from app.services.supabase_client import get_patient_profile, validate_access_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["profile"])


@router.get("/profile")
def get_profile(authorization: str | None = Header(default=None)) -> dict:
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        access_token = authorization.split(" ", 1)[1]
        user_id = validate_access_token(access_token)
        profile = get_patient_profile(user_id)
        return profile if profile else {}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Profile error: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {exc}") from exc