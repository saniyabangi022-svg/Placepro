from ..dao.candidate_dao import CandidateDAO
from ..dao.lookup_dao import LookupDAO
from ..exception.errors import CandidateNotFoundError, DuplicateRecordError, ValidationFailedError
from ..model.entities import Candidate
from ..util.codes import next_code
from ..util.db import session
from ..util.logger import log_activity
from .common import blank_to_none, one_of

PROFILE = ["ACTIVE", "INACTIVE", "ON_HOLD", "BLACKLISTED"]


def _skill_items(cur, data):
    names = data.get("skills") or []
    sm = LookupDAO.skill_map(cur)
    prim = (data.get("primary_technology") or "").lower()
    items = []
    for n in names:
        if n.lower() not in sm:
            raise ValidationFailedError(f"Unknown skill: {n}", {"skills": f"Unknown skill {n}"})
        items.append({"skill_id": sm[n.lower()], "proficiency_level": data.get("skill_level"),
                      "years_experience": data.get("years_experience"), "is_primary": 1 if n.lower() == prim else 0})
    if prim in sm and prim not in [n.lower() for n in names]:
        items.append({"skill_id": sm[prim], "proficiency_level": data.get("skill_level"),
                      "years_experience": data.get("years_experience"), "is_primary": 1})
    return items


def _prepare(data):
    d = blank_to_none(data)
    d["profile_status"] = one_of(d.get("profile_status") or "ACTIVE", PROFILE, "profile_status")
    d["backlog_count"] = 0 if d.get("backlog_count") is None else d["backlog_count"]
    Candidate(**{k: v for k, v in d.items() if k in Candidate.__dataclass_fields__}).validate()
    return d


def _check_duplicates(cur, d, exclude=0):
    if CandidateDAO.taken(cur, "email", d["email"], exclude): raise DuplicateRecordError("Duplicate email not allowed.", {"email": "This email is already registered."})
    if CandidateDAO.taken(cur, "mobile", d["mobile"], exclude): raise DuplicateRecordError("Duplicate mobile not allowed.", {"mobile": "This mobile number is already registered."})


def create_candidate(data, user_id):
    d = _prepare(data)
    with session() as cur:
        _check_duplicates(cur, d)
        d["candidate_code"] = next_code(cur, "candidate")
        cid = CandidateDAO.insert(cur, d)
        CandidateDAO.replace_skills(cur, cid, _skill_items(cur, d))
    log_activity(user_id, "CANDIDATE", "CREATE", d["candidate_code"], f"Candidate {d['full_name']} created")
    return get_candidate(cid)


def update_candidate(cid, data, user_id):
    d = _prepare(data)
    with session() as cur:
        old = CandidateDAO.find(cur, cid)
        if not old: raise CandidateNotFoundError("Candidate not found.")
        _check_duplicates(cur, d, cid)
        CandidateDAO.update(cur, cid, d)
        CandidateDAO.replace_skills(cur, cid, _skill_items(cur, d))
    log_activity(user_id, "CANDIDATE", "UPDATE", old["candidate_code"], "Candidate updated")
    return get_candidate(cid)


def deactivate_candidate(cid, user_id):
    with session() as cur:
        c = CandidateDAO.find(cur, cid)
        if not c: raise CandidateNotFoundError("Candidate not found.")
        CandidateDAO.set_profile_status(cur, cid, "INACTIVE")   # soft deactivate, never hard delete
    log_activity(user_id, "CANDIDATE", "DEACTIVATE", c["candidate_code"], "Candidate deactivated")
    return {"candidate_id": cid, "profile_status": "INACTIVE"}


def list_candidates(filters, page=1, size=20):
    with session() as cur:
        return CandidateDAO.search(cur, filters, page, size)


def get_candidate(cid):
    with session() as cur:
        c = CandidateDAO.find(cur, cid)
        if not c: raise CandidateNotFoundError("Candidate not found.")
        return {**c, "skills": CandidateDAO.skills(cur, cid), "applications": CandidateDAO.applications(cur, cid),
                "interviews": CandidateDAO.interviews(cur, cid), "offers": CandidateDAO.offers(cur, cid)}
