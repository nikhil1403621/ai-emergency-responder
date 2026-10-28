from typing import Dict, Set, Optional


VALID_TRANSITIONS: Dict[str, Set[str]] = {
    "reported": {"under_review", "assessed", "cancelled"},
    "under_review": {"assessed", "dispatched", "cancelled"},
    "assessed": {"under_review", "dispatched", "cancelled"},
    "dispatched": {"en_route", "cancelled", "escalated"},
    "en_route": {"arrived", "dispatched", "escalated"},
    "arrived": {"assistance_in_progress", "resolved", "escalated"},
    "assistance_in_progress": {"resolved", "escalated"},
    "resolved": {"closed", "reopened"},
    "closed": {"reopened"},
    "cancelled": {"reopened"},
    "escalated": {"dispatched", "en_route", "arrived", "assistance_in_progress", "resolved"},
    "reopened": {"under_review", "assessed", "dispatched"}
}


def can_transition(current_status: str, target_status: str) -> bool:
    allowed = VALID_TRANSITIONS.get(current_status, set())
    return target_status in allowed


def validate_transition(current_status: str, target_status: str) -> None:
    if current_status == target_status:
        return
    if not can_transition(current_status, target_status):
        allowed_list = sorted(list(VALID_TRANSITIONS.get(current_status, set())))
        raise ValueError(
            f"Invalid status transition from '{current_status}' to '{target_status}'. "
            f"Allowed next statuses: {', '.join(allowed_list) if allowed_list else 'None (Terminal state)'}"
        )
