"""Routes: applications, interviews, offers/placements, reports, dashboard, activity log."""
from typing import Optional
from fastapi import APIRouter, Depends

from ...dao.lookup_dao import LookupDAO
from ...exception.errors import NotFoundError
from ...reports import report_queries as rq
from ...service import application_service as ap, interview_service as iv, offer_service as of
from ...util.db import session
from ..deps import ADMIN_ONLY, PLACEMENT, RECRUITING, current_user
from ..schemas import ApplyIn, EligibilityIn, FeedbackIn, InterviewIn, JoiningIn, OfferIn, RescheduleIn, StatusIn

applications = APIRouter(prefix="/applications", tags=["Applications"])
interviews = APIRouter(prefix="/interviews", tags=["Interviews"])
offers = APIRouter(tags=["Offers & Placements"])
reports = APIRouter(tags=["Reports"])
activity = APIRouter(prefix="/activity-logs", tags=["Activity"])


@applications.get("")
def list_apps(application_code: Optional[str] = None, candidate: Optional[str] = None, company_id: Optional[int] = None, job: Optional[str] = None,
              status: Optional[str] = None, eligibility: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None,
              job_id: Optional[int] = None, candidate_id: Optional[int] = None, page: int = 1, page_size: int = 20, u=Depends(current_user)):
    f = {k: v for k, v in locals().items() if k not in ("page", "page_size", "u")}
    return ap.list_applications(f, max(page, 1), min(max(page_size, 1), 100))


@applications.post("", status_code=201)
def apply(b: ApplyIn, u=Depends(RECRUITING)): return ap.apply(b.candidate_id, b.job_id, b.source, b.assigned_recruiter_id, u["user_id"])


@applications.post("/eligibility/check")
def check(b: EligibilityIn, u=Depends(current_user)): return ap.preview_eligibility(b.candidate_id, b.job_id)


@applications.get("/{aid}")
def get_app(aid: int, u=Depends(current_user)): return ap.get_application(aid)


@applications.post("/{aid}/recheck")
def recheck(aid: int, u=Depends(RECRUITING)): return ap.recheck(aid, u["user_id"])


@applications.patch("/{aid}/status")
def status(aid: int, b: StatusIn, u=Depends(RECRUITING)): return ap.change_status(aid, b.status, b.remarks, u["user_id"])


@applications.get("/{aid}/history")
def history(aid: int, u=Depends(current_user)): return ap.history(aid)


@interviews.get("")
def list_interviews(candidate: Optional[str] = None, company_id: Optional[int] = None, status: Optional[str] = None, date: Optional[str] = None,
                    application_id: Optional[int] = None, u=Depends(current_user)):
    return iv.list_interviews({k: v for k, v in locals().items() if k != "u"})


@interviews.post("", status_code=201)
def schedule(b: InterviewIn, u=Depends(RECRUITING)): return iv.schedule(b.model_dump(), u["user_id"])


@interviews.patch("/{iid}/reschedule")
def reschedule(iid: int, b: RescheduleIn, u=Depends(RECRUITING)): return iv.reschedule(iid, b.scheduled_date, b.scheduled_time, u["user_id"])


@interviews.patch("/{iid}/no-show")
def no_show(iid: int, u=Depends(RECRUITING)): return iv.mark_no_show(iid, u["user_id"])


@interviews.post("/{iid}/feedback", status_code=201)
def feedback(iid: int, b: FeedbackIn, u=Depends(RECRUITING)): return iv.add_feedback(iid, b.model_dump(), u["user_id"])


@offers.get("/offers")
def list_offers(u=Depends(current_user)): return of.list_offers()


@offers.get("/offers/by-application/{aid}")
def offer_for_app(aid: int, u=Depends(current_user)):
    with session() as cur:
        from ...dao.offer_dao import OfferDAO
        o = OfferDAO.find_by_application(cur, aid)
    if not o: raise NotFoundError("No offer exists for this application yet.")
    return o


@offers.post("/offers", status_code=201)
def create_offer(b: OfferIn, u=Depends(PLACEMENT)): return of.create_offer(b.model_dump(), u["user_id"])


@offers.patch("/offers/{oid}/status")
def offer_status(oid: int, b: StatusIn, u=Depends(PLACEMENT)): return of.update_status(oid, b.status, b.remarks, u["user_id"])


@offers.post("/offers/{oid}/joining")
def joining(oid: int, b: JoiningIn, u=Depends(PLACEMENT)): return of.confirm_joining(oid, b.model_dump(), u["user_id"])


@offers.get("/placements")
def placements(u=Depends(current_user)): return of.list_placements()


@reports.get("/dashboard")
def dashboard(u=Depends(current_user)): return rq.dashboard()


@reports.get("/reports")
def all_reports(u=Depends(current_user)): return rq.all_reports()


@reports.get("/reports/{name}")
def one_report(name: str, u=Depends(current_user)):
    if name not in rq.QUERIES and name not in ("recruitment_funnel", "offer_to_joining"):
        raise NotFoundError("Unknown report.")
    return rq.run(name)


@activity.get("")
def logs(user_id: Optional[int] = None, module: Optional[str] = None, date: Optional[str] = None, u=Depends(ADMIN_ONLY)):
    with session() as cur: return LookupDAO.activity(cur, {"user_id": user_id, "module": module, "date": date})
