from ..dao.application_dao import ApplicationDAO
from ..dao.candidate_dao import CandidateDAO
from ..dao.job_dao import JobDAO
from ..exception.errors import (ApplicationNotFoundError, CandidateNotEligibleError, CandidateNotFoundError,
                                DuplicateApplicationError, InvalidStatusTransitionError, JobNotFoundError, ValidationFailedError)
from ..util.codes import next_code
from ..util.db import session
from ..util.logger import log_activity
from .eligibility import check_eligibility
from .workflow import MANUAL_TARGETS, validate_transition


def transition(cur, app, new_status, remarks, user_id):
    """Shared by every service: validate -> update application -> insert history (same transaction)."""
    validate_transition(app["application_status"], new_status)
    ApplicationDAO.set_status(cur, app["application_id"], new_status)
    ApplicationDAO.add_history(cur, app["application_id"], app["application_status"], new_status, remarks, user_id)
    app["application_status"] = new_status


def _evaluate(cur, candidate_id, job_id, ignore_existing=False):
    cand = CandidateDAO.find(cur, candidate_id)
    if not cand: raise CandidateNotFoundError("Candidate not found.")
    job = JobDAO.find(cur, job_id)
    if not job: raise JobNotFoundError("Job not found.")
    applied = False if ignore_existing else ApplicationDAO.exists(cur, candidate_id, job_id)
    res = check_eligibility(cand, job, JobDAO.skills(cur, job_id), CandidateDAO.skills(cur, candidate_id), applied)
    return cand, job, res, applied


def preview_eligibility(candidate_id, job_id):
    """Used by the 'Check Eligibility' button - nothing is saved."""
    with session() as cur:
        return _evaluate(cur, candidate_id, job_id)[2]


def apply(candidate_id, job_id, source, recruiter_id, user_id):
    with session() as cur:
        cand, job, res, applied = _evaluate(cur, candidate_id, job_id)
        if applied: raise DuplicateApplicationError("Candidate has already applied for this job.")
        if not res["eligible"]: raise CandidateNotEligibleError("NOT ELIGIBLE: " + res["reason"], res["reasons"])
        code = next_code(cur, "application")
        aid = ApplicationDAO.insert(cur, {"application_code": code, "candidate_id": candidate_id, "job_id": job_id, "eligibility_status": "ELIGIBLE",
                                          "eligibility_reason": res["reason"], "application_status": "APPLIED", "source": source or "Portal",
                                          "assigned_recruiter_id": recruiter_id or user_id})
        ApplicationDAO.add_history(cur, aid, None, "APPLIED", "Application created", user_id)
    log_activity(user_id, "APPLICATION", "CREATE", code, f"{cand['full_name']} applied for {job['job_code']}")
    return get_application(aid)


def recheck(application_id, user_id):
    with session() as cur:
        app = ApplicationDAO.find(cur, application_id, lock=True)
        if not app: raise ApplicationNotFoundError("Application not found.")
        _, _, res, _ = _evaluate(cur, app["candidate_id"], app["job_id"], ignore_existing=True)
        ApplicationDAO.set_eligibility(cur, application_id, res["status"], res["reason"])
        if res["eligible"] and app["application_status"] == "APPLIED":
            transition(cur, app, "ELIGIBILITY_VERIFIED", "Eligibility verified", user_id)
    log_activity(user_id, "APPLICATION", "ELIGIBILITY", application_id, res["status"])
    return {**res, "application": get_application(application_id)}


def change_status(application_id, new_status, remarks, user_id):
    if new_status not in MANUAL_TARGETS:
        raise InvalidStatusTransitionError(f"{new_status} is set automatically by the interview / offer / placement steps.")
    with session() as cur:
        app = ApplicationDAO.find(cur, application_id, lock=True)
        if not app: raise ApplicationNotFoundError("Application not found.")
        if new_status == "SHORTLISTED" and app["eligibility_status"] != "ELIGIBLE":
            raise CandidateNotEligibleError("Only ELIGIBLE applications can be shortlisted.")
        transition(cur, app, new_status, remarks, user_id)
    log_activity(user_id, "APPLICATION", new_status, application_id, remarks or "Status changed")
    return get_application(application_id)


def list_applications(filters, page=1, size=20):
    with session() as cur: return ApplicationDAO.search(cur, filters, page, size)


def get_application(aid):
    with session() as cur:
        a = ApplicationDAO.find(cur, aid)
        if not a: raise ApplicationNotFoundError("Application not found.")
        return a


def history(aid):
    with session() as cur:
        if not ApplicationDAO.find(cur, aid): raise ApplicationNotFoundError("Application not found.")
        return ApplicationDAO.history(cur, aid)
