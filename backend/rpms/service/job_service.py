from ..dao.company_dao import CompanyDAO
from ..dao.job_dao import JobDAO
from ..dao.lookup_dao import LookupDAO
from ..exception.errors import CompanyNotFoundError, DuplicateRecordError, JobNotFoundError, ValidationFailedError
from ..model.entities import Job
from ..util.db import session
from ..util.logger import log_activity
from .common import blank_to_none, one_of

JOB_STATUS = ["DRAFT", "OPEN", "CLOSED", "CANCELLED"]
EMP = ["FULL_TIME", "INTERNSHIP", "CONTRACT"]


def _prepare(data):
    d = blank_to_none(data)
    d["employment_type"] = one_of(d.get("employment_type") or "FULL_TIME", EMP, "employment_type")
    d["status"] = one_of(d.get("status") or "OPEN", JOB_STATUS, "status")
    d["max_backlogs"] = d.get("max_backlogs") if d.get("max_backlogs") is not None else 0
    d["experience_min_years"] = d.get("experience_min_years") or 0
    if isinstance(d.get("qualifications"), list): d["qualification_rule"] = "/".join(d["qualifications"]) or None
    Job(**{k: v for k, v in d.items() if k in Job.__dataclass_fields__ and k != "skills"}).validate()
    return d


def _skill_rows(cur, d):
    sm = LookupDAO.skill_map(cur)
    rows, mand = {}, 0 if (d.get("skill_type") or "Mandatory").lower() == "preferred" else 1
    for n in d.get("required_skills") or []:
        rows[n.lower()] = {"name": n, "mandatory_flag": mand}
    if d.get("required_technology"):   # the main technology is always mandatory
        rows[d["required_technology"].lower()] = {"name": d["required_technology"], "mandatory_flag": 1}
    out = []
    for key, r in rows.items():
        if key not in sm: raise ValidationFailedError(f"Unknown skill: {r['name']}", {"required_skills": f"Unknown skill {r['name']}"})
        out.append({"skill_id": sm[key], "minimum_level": d.get("minimum_level"), "mandatory_flag": r["mandatory_flag"]})
    return out


def create_job(data, user_id):
    d = _prepare(data); d["created_by"] = user_id
    with session() as cur:
        co = CompanyDAO.find(cur, d.get("company_id"))
        if not co: raise CompanyNotFoundError("Company not found.")
        if co["status"] != "ACTIVE": raise ValidationFailedError("Company is INACTIVE.", {"company_id": "Company is inactive."})
        try:
            jid = JobDAO.insert(cur, d)
        except DuplicateRecordError:
            raise DuplicateRecordError("Job code already exists.", {"job_code": "This job code is already used."})
        JobDAO.replace_skills(cur, jid, _skill_rows(cur, d))
    log_activity(user_id, "JOB", "CREATE", d["job_code"], f"Job {d['job_title']} created")
    return get_job(jid)


def update_job(jid, data, user_id):
    d = _prepare(data)
    with session() as cur:
        if not JobDAO.find(cur, jid): raise JobNotFoundError("Job not found.")
        JobDAO.update(cur, jid, d)
        JobDAO.replace_skills(cur, jid, _skill_rows(cur, d))
    log_activity(user_id, "JOB", "UPDATE", jid, "Job updated")
    return get_job(jid)


def close_job(jid, user_id):
    with session() as cur:
        j = JobDAO.find(cur, jid)
        if not j: raise JobNotFoundError("Job not found.")
        if j["status"] in ("CLOSED", "CANCELLED"): raise ValidationFailedError(f"Job is already {j['status']}.")
        JobDAO.set_status(cur, jid, "CLOSED")           # CLOSED/CANCELLED instead of delete
    log_activity(user_id, "JOB", "CLOSE", j["job_code"], "Job closed")
    return get_job(jid)


def list_jobs(filters, page=1, size=20):
    with session() as cur:
        r = JobDAO.search(cur, filters, page, size)
        r["summary"] = cur.one("SELECT SUM(status='OPEN') AS open_jobs,SUM(CASE WHEN status='OPEN' THEN openings ELSE 0 END) AS total_openings,"
                               "SUM(status='OPEN' AND application_deadline BETWEEN CURDATE() AND DATE_ADD(CURDATE(),INTERVAL 7 DAY)) AS closing_this_week,"
                               "SUM(status='DRAFT') AS draft FROM jobs")
        return r


def get_job(jid):
    with session() as cur:
        j = JobDAO.find(cur, jid)
        if not j: raise JobNotFoundError("Job not found.")
        return {**j, "skills": JobDAO.skills(cur, jid)}
