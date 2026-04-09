import os
from typing import Optional

from supabase import Client, create_client


def get_supabase_client() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        return None

    return create_client(url, key)


def validate_access_token(access_token: str) -> str:
    client = get_supabase_client()
    if client is None or not access_token:
        raise ValueError("Supabase is not configured")

    user = client.auth.get_user(access_token)
    user_data = getattr(user, "user", None)
    user_id = getattr(user_data, "id", None)

    if not user_id:
        raise ValueError("Invalid or expired access token")
    return user_id


def save_chat_history(
    user_id: str,
    user_message: str,
    ai_response: str,
    response_type: str,
    severity: str = "low",
    emergency: bool = False,
    current_symptom: str | None = None,
) -> None:
    client = get_supabase_client()
    if client is None:
        # Supabase is optional during local setup; skip DB write when not configured.
        return

    # Start with required fields
    payload = {
        "user_id": user_id,
        "user_message": user_message,
        "ai_response": ai_response,
        "response_type": response_type,
    }
    
    # Try to save, handling both old and new database schemas
    try:
        # Try with new fields first (if database has been updated)
        payload_with_new_fields = {
            **payload,
            "severity": severity,
            "emergency": emergency,
            "current_symptom": current_symptom,
        }
        client.table("chat_history").insert(payload_with_new_fields).execute()
    except Exception:
        # Fallback to original fields if new columns don't exist yet
        try:
            client.table("chat_history").insert(payload).execute()
        except Exception:
            # Silently fail if database write doesn't work
            pass


def get_chat_history(user_id: str) -> list[dict]:
    client = get_supabase_client()
    if client is None:
        return []

    try:
        # Try to get chat history with new fields first
        result = (
            client.table("chat_history")
            .select("user_message, ai_response, response_type, severity, emergency, current_symptom, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []
    except Exception:
        # Fallback to original fields if new columns don't exist
        try:
            result = (
                client.table("chat_history")
                .select("user_message, ai_response, response_type, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=False)
                .execute()
            )
            return result.data or []
        except Exception:
            # Return empty list if query fails
            return []


def get_patient_profile(user_id: str) -> dict:
    client = get_supabase_client()
    if client is None:
        return {}

    try:
        result = (
            client.table("profiles")
            .select("appointment_id, full_name, age, gender, phone, address, created_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        profile_data = result.data or {}
        # Ensure empty objects are returned consistently
        return profile_data
    except Exception as e:
        # Fallback: try to get any available profile data
        try:
            result = (
                client.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
            profile_data = result.data or {}
            return profile_data
        except Exception as fallback_error:
            # Log but don't crash - return empty dict
            return {}
