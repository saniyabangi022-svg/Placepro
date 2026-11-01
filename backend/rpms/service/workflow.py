"""Recruitment workflow rules: which status may follow which. Invalid jumps (APPLIED -> JOINED) are rejected."""
from ..exception.errors import InvalidStatusTransitionError

TRANSITIONS = {
    "APPLIED": {"ELIGIBILITY_VERIFIED", "SHORTLISTED", "REJECTED", "WITHDRAWN"},
    "ELIGIBILITY_VERIFIED": {"SHORTLISTED", "REJECTED", "WITHDRAWN"},
    "SHORTLISTED": {"INTERVIEW_SCHEDULED", "REJECTED", "WITHDRAWN"},
    "INTERVIEW_SCHEDULED": {"INTERVIEWED", "REJECTED", "WITHDRAWN"},
    "INTERVIEWED": {"INTERVIEW_SCHEDULED", "SELECTED", "REJECTED", "WITHDRAWN"},   # INTERVIEW_SCHEDULED = next round
    "SELECTED": {"OFFERED", "REJECTED", "WITHDRAWN"},
    "OFFERED": {"JOINED", "WITHDRAWN", "REJECTED"},
    "JOINED": set(), "REJECTED": set(), "WITHDRAWN": set(),
}
MANUAL_TARGETS = {"ELIGIBILITY_VERIFIED", "SHORTLISTED", "REJECTED", "WITHDRAWN"}   # others are driven by interview/offer/placement steps


def validate_transition(old, new):
    if new not in TRANSITIONS.get(old, set()):
        allowed = ", ".join(sorted(TRANSITIONS.get(old, []))) or "none (final status)"
        raise InvalidStatusTransitionError(f"Invalid status change {old} -> {new}. Allowed next: {allowed}.")
