"""Pure-logic tests: no database needed.   pytest tests/test_unit.py"""
from datetime import date, timedelta
import pytest
from rpms.exception.errors import InvalidStatusTransitionError, ValidationFailedError
from rpms.service.eligibility import check_eligibility
from rpms.service.workflow import validate_transition
from rpms.util import validators

T = date.today()
JOB = {"status": "OPEN", "application_deadline": T + timedelta(days=5), "qualification_rule": "BE/BTech/MCA", "min_percentage": 60,
       "min_passing_year": 2024, "max_passing_year": 2026, "max_backlogs": 0}
CAND = {"profile_status": "ACTIVE", "qualification": "BE", "percentage": 70, "passing_year": 2025, "backlog_count": 0, "primary_technology": "Java"}
SK = [{"skill_name": "Java", "mandatory_flag": 1, "minimum_level": None}]


def test_eligible():
    r = check_eligibility(CAND, JOB, SK, [{"skill_name": "Java", "proficiency_level": "BASIC"}])
    assert r["eligible"] and r["status"] == "ELIGIBLE"


@pytest.mark.parametrize("change,text", [({"percentage": 59.5}, "below required"), ({"backlog_count": 1}, "Backlogs"),
                                         ({"passing_year": 2027}, "after"), ({"qualification": "BCA"}, "Qualification"),
                                         ({"profile_status": "INACTIVE"}, "not ACTIVE")])
def test_not_eligible(change, text):
    r = check_eligibility({**CAND, **change}, JOB, SK, [])
    assert not r["eligible"] and text in r["reason"]


def test_job_closed_deadline_duplicate_and_skill():
    assert "not OPEN" in check_eligibility(CAND, {**JOB, "status": "CLOSED"}, SK, [])["reason"]
    assert "passed" in check_eligibility(CAND, {**JOB, "application_deadline": T - timedelta(days=1)}, SK, [])["reason"]
    assert "already applied" in check_eligibility(CAND, JOB, SK, [], already_applied=True)["reason"]
    r = check_eligibility({**CAND, "primary_technology": "Python"}, JOB, SK, [])
    assert "Missing mandatory skill Java" in r["reason"]


def test_workflow_rules():
    validate_transition("APPLIED", "SHORTLISTED")
    validate_transition("SELECTED", "OFFERED")
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition("APPLIED", "JOINED")
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition("REJECTED", "SHORTLISTED")


def test_validators():
    good = {"full_name": "A", "email": "a@b.co", "mobile": "9876543210", "percentage": 70, "backlog_count": 0, "qualification": "BE", "passing_year": 2025}
    validators.check_candidate(good)
    for bad, field in [({"percentage": 101}, "percentage"), ({"backlog_count": -1}, "backlog_count"), ({"mobile": "123"}, "mobile"), ({"email": "x"}, "email")]:
        with pytest.raises(ValidationFailedError) as e:
            validators.check_candidate({**good, **bad})
        assert field in e.value.details
