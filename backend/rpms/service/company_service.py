from ..dao.company_dao import CompanyDAO
from ..exception.errors import CompanyNotFoundError, ValidationFailedError
from ..util.codes import next_code
from ..util.db import session
from ..util.logger import log_activity
from ..util.validators import EMAIL, collect
from .common import blank_to_none, one_of

TYPES = ["MNC", "STARTUP", "MID_SIZE", "CONSULTANCY"]


def _prepare(data):
    d = blank_to_none(data)
    e = {}
    if not d.get("company_name"): e["company_name"] = "Company name is required."
    if d.get("hr_email") and not EMAIL.match(d["hr_email"]): e["hr_email"] = "Enter a valid email address."
    collect(e)
    if d.get("company_type"): one_of(d["company_type"], TYPES, "company_type")
    d["status"] = one_of(d.get("status") or "ACTIVE", ["ACTIVE", "INACTIVE"], "status")
    return d


def create_company(data, user_id):
    d = _prepare(data)
    with session() as cur:
        d["company_code"] = next_code(cur, "company")
        cid = CompanyDAO.insert(cur, d)
    log_activity(user_id, "COMPANY", "CREATE", d["company_code"], f"Company {d['company_name']} created")
    return get_company(cid)


def update_company(cid, data, user_id):
    d = _prepare(data)
    with session() as cur:
        if not CompanyDAO.find(cur, cid): raise CompanyNotFoundError("Company not found.")
        CompanyDAO.update(cur, cid, d)
    log_activity(user_id, "COMPANY", "UPDATE", cid, "Company updated")
    return get_company(cid)


def set_status(cid, status, user_id):
    one_of(status, ["ACTIVE", "INACTIVE"], "status")
    with session() as cur:
        if not CompanyDAO.find(cur, cid): raise CompanyNotFoundError("Company not found.")
        CompanyDAO.set_status(cur, cid, status)        # INACTIVE instead of delete
    log_activity(user_id, "COMPANY", "STATUS", cid, f"Company set {status}")
    return get_company(cid)


def list_companies(filters):
    with session() as cur: return CompanyDAO.search(cur, filters)


def get_company(cid):
    with session() as cur:
        c = CompanyDAO.find(cur, cid)
        if not c: raise CompanyNotFoundError("Company not found.")
        return c
