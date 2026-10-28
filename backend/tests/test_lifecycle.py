import pytest
from app.services.lifecycle import validate_transition, can_transition


def test_valid_forward_lifecycle_transitions():
    # reported -> under_review -> assessed -> dispatched -> en_route -> arrived -> assistance_in_progress -> resolved -> closed
    validate_transition("reported", "under_review")
    validate_transition("under_review", "assessed")
    validate_transition("assessed", "dispatched")
    validate_transition("dispatched", "en_route")
    validate_transition("en_route", "arrived")
    validate_transition("arrived", "assistance_in_progress")
    validate_transition("assistance_in_progress", "resolved")
    validate_transition("resolved", "closed")


def test_reopen_and_cancellation():
    validate_transition("reported", "cancelled")
    validate_transition("resolved", "reopened")
    validate_transition("closed", "reopened")
    validate_transition("reopened", "dispatched")


def test_invalid_transition_raises_error():
    # Cannot jump straight from reported to resolved or closed
    with pytest.raises(ValueError, match="Invalid status transition"):
        validate_transition("reported", "resolved")

    with pytest.raises(ValueError, match="Invalid status transition"):
        validate_transition("reported", "closed")

    # Cannot jump from arrived directly back to reported
    with pytest.raises(ValueError, match="Invalid status transition"):
        validate_transition("arrived", "reported")


def test_idempotent_same_status():
    # Transition to same status does nothing
    validate_transition("dispatched", "dispatched")
    validate_transition("reported", "reported")
