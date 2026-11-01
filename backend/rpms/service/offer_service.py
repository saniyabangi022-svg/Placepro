from datetime import date

from ..dao.application_dao import ApplicationDAO
from ..dao.candidate_dao import CandidateDAO
from ..dao.job_dao import JobDAO
from ..dao.offer_dao import OfferDAO
from ..exception.errors import (ApplicationNotFoundError, DuplicateRecordError, InvalidStatusTransitionError,
                                OfferNotFoundError, ValidationFailedError)
from ..util.codes import next_code
from ..util.db import session
from ..util.logger import log_activity
from .application_service import transition
from .common import blank_to_none, one_of

OFFER_STATUS = ["OFFERED", "ACCEPTED", "REJECTED", "EXPIRED", "WITHDRAWN"]
JOINING = ["PENDING", "JOINED", "NOT_JOINED", "DEFERRED", "NO_SHOW"]


def create_offer(data, user_id):
    d = blank_to_none(data)
    e = {}
    if not d.get("designation"): e["designation"] = "Designation is required."
    if d.get("offered_package_lpa") is None or float(d["offered_package_lpa"]) <= 0: e["offered_package_lpa"] = "Package must be greater than zero."
    if not d.get("offer_date"): e["offer_date"] = "Offer date is required."
    elif d.get("expected_joining_date") and d["expected_joining_date"] < d["offer_date"]: e["expected_joining_date"] = "Joining date cannot be before the offer date."
    if e: raise ValidationFailedError("Please correct the highlighted fields.", e)
    with session() as cur:                      # selection -> offer -> application status -> history
        app = ApplicationDAO.find(cur, d.get("application_id"), lock=True)
        if not app: raise ApplicationNotFoundError("Application not found.")
        if app["application_status"] != "SELECTED":
            raise InvalidStatusTransitionError(f"An offer can only be created for a SELECTED application (current: {app['application_status']}).")
        if OfferDAO.find_by_application(cur, app["application_id"]): raise DuplicateRecordError("An offer already exists for this application.")
        d["offer_code"] = next_code(cur, "offer")
        oid = OfferDAO.insert(cur, d)
        transition(cur, app, "OFFERED", f"Offer {d['offer_code']} created", user_id)
    log_activity(user_id, "OFFER", "CREATE", d["offer_code"], f"{d['designation']} @ {d['offered_package_lpa']} LPA")
    return get_offer(oid)


def update_status(oid, status, remarks, user_id):
    one_of(status, OFFER_STATUS, "offer_status")
    with session() as cur:
        o = OfferDAO.find(cur, oid)
        if not o: raise OfferNotFoundError("Offer not found.")
        ok = (o["offer_status"] == "OFFERED" and status != "OFFERED") or (o["offer_status"] == "ACCEPTED" and status == "WITHDRAWN" and o["joining_status"] != "JOINED")
        if not ok: raise InvalidStatusTransitionError(f"Offer cannot change from {o['offer_status']} to {status}.")
        OfferDAO.set_status(cur, oid, status, remarks)
        if status in ("REJECTED", "EXPIRED", "WITHDRAWN"):
            app = ApplicationDAO.find(cur, o["application_id"], lock=True)
            transition(cur, app, "WITHDRAWN", f"Offer {status.lower()}", user_id)
    log_activity(user_id, "OFFER", status, o["offer_code"], remarks or "Offer status changed")
    return get_offer(oid)


def confirm_joining(oid, data, user_id):
    d = blank_to_none(data)
    one_of(d.get("joining_status"), JOINING, "joining_status")
    d["placement_status"] = one_of(d.get("placement_status") or "ACTIVE", ["ACTIVE", "CANCELLED"], "placement_status")
    if d["joining_status"] == "JOINED" and not d.get("actual_joining_date"):
        d["actual_joining_date"] = date.today().isoformat()
    if d.get("final_package_lpa") is not None and float(d["final_package_lpa"]) <= 0:
        raise ValidationFailedError("Final package must be greater than zero.", {"final_package_lpa": "Package must be greater than zero."})
    with session() as cur:   # joining -> placement -> candidate PLACED -> application JOINED -> history
        o = OfferDAO.find(cur, oid)
        if not o: raise OfferNotFoundError("Offer not found.")
        if o["offer_status"] != "ACCEPTED": raise InvalidStatusTransitionError("Placement needs an ACCEPTED offer.")
        app = ApplicationDAO.find(cur, o["application_id"], lock=True)
        job = JobDAO.find(cur, app["job_id"])
        row = {"designation": d.get("designation") or o["designation"], "final_package_lpa": d.get("final_package_lpa") or o["offered_package_lpa"],
               "actual_joining_date": d.get("actual_joining_date"), "joining_status": d["joining_status"], "placement_status": d["placement_status"]}
        existing = OfferDAO.placement_for_offer(cur, oid)
        if existing: OfferDAO.update_placement(cur, existing["placement_id"], row)
        else: OfferDAO.insert_placement(cur, {**row, "candidate_id": app["candidate_id"], "company_id": job["company_id"], "job_id": app["job_id"],
                                              "offer_id": oid, "expected_joining_date": o["expected_joining_date"]})
        joined = row["joining_status"] == "JOINED" and row["placement_status"] == "ACTIVE"
        if joined:
            CandidateDAO.set_placement_status(cur, app["candidate_id"], "PLACED")
            if app["application_status"] == "OFFERED": transition(cur, app, "JOINED", "Joining confirmed", user_id)
        elif OfferDAO.active_joined_count(cur, app["candidate_id"]) == 0:
            CandidateDAO.set_placement_status(cur, app["candidate_id"], "NOT_PLACED")
    log_activity(user_id, "PLACEMENT", "JOINING_" + row["joining_status"], o["offer_code"], f"Placement {row['placement_status']}")
    return get_offer(oid)


def list_offers():
    with session() as cur: return OfferDAO.list(cur)


def list_placements():
    with session() as cur: return OfferDAO.placements(cur)


def get_offer(oid):
    with session() as cur:
        o = OfferDAO.find(cur, oid)
        if not o: raise OfferNotFoundError("Offer not found.")
        return o
