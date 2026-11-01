from datetime import date

from ..dao.application_dao import ApplicationDAO
from ..dao.interview_dao import InterviewDAO
from ..exception.errors import (ApplicationNotFoundError, DuplicateRecordError, InterviewNotFoundError,
                                InvalidStatusTransitionError, ValidationFailedError)
from ..util.db import session
from ..util.logger import log_activity
from .application_service import transition
from .common import blank_to_none, one_of

ROUNDS = ["APTITUDE", "TECHNICAL", "MANAGERIAL", "HR"]
MODES = ["ONLINE", "OFFLINE", "TELEPHONIC"]
RECO = ["NEXT_ROUND", "SELECTED", "REJECTED", "ON_HOLD"]


def schedule(data, user_id):
    d = blank_to_none(data)
    one_of(d.get("round_type"), ROUNDS, "round_type"); one_of(d.get("mode"), MODES, "mode")
    if not d.get("round_number") or int(d["round_number"]) < 1: raise ValidationFailedError("Round number must be 1 or more.", {"round_number": "Round number must be 1 or more."})
    try:
        if date.fromisoformat(str(d["scheduled_date"])) < date.today():
            raise ValidationFailedError("Interview date cannot be in the past.", {"scheduled_date": "Interview date cannot be in the past."})
    except (KeyError, ValueError):
        raise ValidationFailedError("Valid interview date is required.", {"scheduled_date": "Valid interview date is required."})
    with session() as cur:
        app = ApplicationDAO.find(cur, d.get("application_id"), lock=True)
        if not app: raise ApplicationNotFoundError("Application not found.")
        if app["application_status"] not in ("SHORTLISTED", "INTERVIEWED"):
            raise InvalidStatusTransitionError(f"Cannot schedule an interview for an application in status {app['application_status']}. It must be SHORTLISTED (or INTERVIEWED for the next round).")
        if InterviewDAO.open_round(cur, app["application_id"]): raise DuplicateRecordError("An earlier round is still scheduled. Complete or cancel it first.")
        if InterviewDAO.round_exists(cur, app["application_id"], d["round_number"]): raise DuplicateRecordError("This interview round already exists for the application.", {"round_number": "Round number already used."})
        iid = InterviewDAO.insert(cur, d)
        transition(cur, app, "INTERVIEW_SCHEDULED", f"Round {d['round_number']} {d['round_type']} scheduled", user_id)
    log_activity(user_id, "INTERVIEW", "SCHEDULE", iid, f"Round {d['round_number']} scheduled")
    return get_interview(iid)


def _open_interview(cur, iid):
    i = InterviewDAO.find(cur, iid)
    if not i: raise InterviewNotFoundError("Interview not found.")
    if i["status"] not in ("SCHEDULED", "RESCHEDULED"): raise InvalidStatusTransitionError(f"Interview is already {i['status']}.")
    return i


def reschedule(iid, new_date, new_time, user_id):
    if not new_date or date.fromisoformat(str(new_date)) < date.today():
        raise ValidationFailedError("Interview date cannot be in the past.", {"scheduled_date": "Interview date cannot be in the past."})
    with session() as cur:
        _open_interview(cur, iid); InterviewDAO.reschedule(cur, iid, new_date, new_time or None)
    log_activity(user_id, "INTERVIEW", "RESCHEDULE", iid, f"Moved to {new_date}")
    return get_interview(iid)


def mark_no_show(iid, user_id):
    with session() as cur:
        _open_interview(cur, iid); InterviewDAO.set_status(cur, iid, "NO_SHOW")
    log_activity(user_id, "INTERVIEW", "NO_SHOW", iid, "Candidate did not attend")
    return get_interview(iid)


def add_feedback(iid, data, user_id):
    d = blank_to_none(data)
    one_of(d.get("recommendation"), RECO, "recommendation")
    errs = {}
    for k in ("technical_rating", "communication_rating", "problem_solving_rating", "overall_rating"):
        if d.get(k) is not None and not 0 <= float(d[k]) <= 5: errs[k] = "Rating must be between 0 and 5."
    if errs: raise ValidationFailedError("Rating must be between 0 and 5.", errs)
    if d.get("overall_rating") is None:
        vals = [float(d[k]) for k in ("technical_rating", "communication_rating", "problem_solving_rating") if d.get(k) is not None]
        d["overall_rating"] = round(sum(vals) / len(vals), 1) if vals else None
    with session() as cur:                      # ONE transaction: feedback + interview + application + history
        i = _open_interview(cur, iid)
        if InterviewDAO.feedback_exists(cur, iid): raise DuplicateRecordError("Feedback already submitted for this round.")
        InterviewDAO.insert_feedback(cur, {**d, "interview_id": iid, "submitted_by": user_id})
        InterviewDAO.set_status(cur, iid, "COMPLETED")
        app = ApplicationDAO.find(cur, i["application_id"], lock=True)
        transition(cur, app, "INTERVIEWED", f"Round {i['round_number']} feedback submitted", user_id)
        if d["recommendation"] in ("SELECTED", "REJECTED"):
            transition(cur, app, d["recommendation"], d.get("remarks") or f"Result of round {i['round_number']}", user_id)
    log_activity(user_id, "INTERVIEW", "FEEDBACK", iid, d["recommendation"])
    return get_interview(iid)


def list_interviews(filters):
    with session() as cur:
        rows = InterviewDAO.search(cur, filters)
        stats = cur.one("SELECT SUM(scheduled_date=CURDATE() AND status IN ('SCHEDULED','RESCHEDULED')) AS today,"
                        "SUM(YEARWEEK(scheduled_date,1)=YEARWEEK(CURDATE(),1)) AS this_week,SUM(status='COMPLETED') AS completed,SUM(status='NO_SHOW') AS no_show FROM interview_rounds")
        return {"items": rows, "stats": stats}


def get_interview(iid):
    with session() as cur:
        i = InterviewDAO.find(cur, iid)
        if not i: raise InterviewNotFoundError("Interview not found.")
        return i
