"""Routes: auth, lookups, candidates, companies, jobs. Routes only translate HTTP <-> service calls."""
from typing import Optional
from fastapi import APIRouter, Depends

from ...dao.lookup_dao import LookupDAO
from ...service import auth_service, candidate_service as cs, company_service as co, job_service as js
from ...util.db import session
from ..deps import PLACEMENT, RECRUITING, current_user
from ..schemas import CandidateIn, CompanyIn, JobIn, LoginIn, StatusIn

auth = APIRouter(prefix="/auth", tags=["Auth"])
lookups = APIRouter(prefix="/lookups", tags=["Lookups"])
candidates = APIRouter(prefix="/candidates", tags=["Candidates"])
companies = APIRouter(prefix="/companies", tags=["Companies"])
jobs = APIRouter(prefix="/jobs", tags=["Jobs"])


@auth.post("/login")
def login(b: LoginIn): return auth_service.login(b.username, b.password, b.role)


@auth.get("/me")
def me(u=Depends(current_user)): return u


@lookups.get("")
def get_lookups(u=Depends(current_user)):
    with session() as cur: return LookupDAO.lookups(cur)


@candidates.get("")
def list_candidates(candidate_code: Optional[str] = None, name: Optional[str] = None, mobile: Optional[str] = None, email: Optional[str] = None,
                    primary_technology: Optional[str] = None, passing_year: Optional[int] = None, qualification: Optional[str] = None,
                    profile_status: Optional[str] = None, placement_status: Optional[str] = None, page: int = 1, page_size: int = 20, u=Depends(current_user)):
    f = {k: v for k, v in locals().items() if k not in ("page", "page_size", "u")}
    return cs.list_candidates(f, max(page, 1), min(max(page_size, 1), 100))


@candidates.get("/{cid}")
def get_candidate(cid: int, u=Depends(current_user)): return cs.get_candidate(cid)


@candidates.post("", status_code=201)
def create_candidate(b: CandidateIn, u=Depends(RECRUITING)): return cs.create_candidate(b.model_dump(), u["user_id"])


@candidates.put("/{cid}")
def update_candidate(cid: int, b: CandidateIn, u=Depends(RECRUITING)): return cs.update_candidate(cid, b.model_dump(), u["user_id"])


@candidates.patch("/{cid}/deactivate")
def deactivate_candidate(cid: int, u=Depends(RECRUITING)): return cs.deactivate_candidate(cid, u["user_id"])


@companies.get("")
def list_companies(name: Optional[str] = None, industry: Optional[str] = None, company_type: Optional[str] = None, status: Optional[str] = None, u=Depends(current_user)):
    return co.list_companies({"name": name, "industry": industry, "company_type": company_type, "status": status})


@companies.get("/{cid}")
def get_company(cid: int, u=Depends(current_user)): return co.get_company(cid)


@companies.post("", status_code=201)
def create_company(b: CompanyIn, u=Depends(PLACEMENT)): return co.create_company(b.model_dump(), u["user_id"])


@companies.put("/{cid}")
def update_company(cid: int, b: CompanyIn, u=Depends(PLACEMENT)): return co.update_company(cid, b.model_dump(), u["user_id"])


@companies.patch("/{cid}/status")
def company_status(cid: int, b: StatusIn, u=Depends(PLACEMENT)): return co.set_status(cid, b.status, u["user_id"])


@jobs.get("")
def list_jobs(job_code: Optional[str] = None, company_id: Optional[int] = None, skill: Optional[str] = None, location: Optional[str] = None,
              status: Optional[str] = None, employment_type: Optional[str] = None, page: int = 1, page_size: int = 20, u=Depends(current_user)):
    f = {k: v for k, v in locals().items() if k not in ("page", "page_size", "u")}
    return js.list_jobs(f, max(page, 1), min(max(page_size, 1), 100))


@jobs.get("/{jid}")
def get_job(jid: int, u=Depends(current_user)): return js.get_job(jid)


@jobs.post("", status_code=201)
def create_job(b: JobIn, u=Depends(RECRUITING)): return js.create_job(b.model_dump(), u["user_id"])


@jobs.put("/{jid}")
def update_job(jid: int, b: JobIn, u=Depends(RECRUITING)): return js.update_job(jid, b.model_dump(), u["user_id"])


@jobs.patch("/{jid}/close")
def close_job(jid: int, u=Depends(RECRUITING)): return js.close_job(jid, u["user_id"])
