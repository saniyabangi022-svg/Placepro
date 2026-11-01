"""End-to-end API tests against a REAL MySQL database (needs Phase 3 setup + `python scripts/set_demo_passwords.py`).
   pytest tests/test_api.py        (skipped automatically if the database is not reachable)"""
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from rpms.app.main import app
from rpms.util import db

try:
    db.ping(); DB_UP = True
except Exception:
    DB_UP = False
pytestmark = pytest.mark.skipif(not DB_UP, reason="MySQL not reachable")
import time
RUN = int(time.time()) % 100000          # unique per run, so tests can be repeated
PW = "Placepro@123"
c = TestClient(app)
S = {}


def login(user, role=None):
    r = c.post("/api/auth/login", json={"username": user, "password": PW, "role": role})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def cand(n, **kw):
    return {"full_name": f"Test User {n}", "email": f"t{RUN}{n}@example.com", "mobile": f"9{RUN:05d}{n:04d}", "qualification": "BE", "passing_year": 2025,
            "percentage": 72, "backlog_count": 0, "primary_technology": "Python", "skills": ["Python", "SQL"], "skill_level": "INTERMEDIATE", **kw}


def test_01_auth_and_roles():
    assert c.get("/api/health").json()["database"] == "connected"
    assert c.post("/api/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    assert c.get("/api/candidates").status_code == 401
    S["admin"], S["rec"], S["po"] = login("admin"), login("amit.recruiter", "RECRUITER"), login("neha.placement", "PLACEMENT_OFFICER")
    assert c.post("/api/companies", json={"company_name": "X"}, headers=S["rec"]).status_code == 403


def test_02_candidate_rules():
    H = S["rec"]
    r = c.post("/api/candidates", json=cand(1), headers=H); assert r.status_code == 201, r.text
    S["c1"] = r.json()["candidate_id"]; assert r.json()["candidate_code"].startswith("CAN-")
    assert c.post("/api/candidates", json=cand(1, mobile="9000012345"), headers=H).status_code == 409      # duplicate email
    assert c.post("/api/candidates", json=cand(2, mobile=cand(1)["mobile"]), headers=H).status_code == 409  # duplicate mobile
    assert c.post("/api/candidates", json=cand(3, percentage=101), headers=H).status_code == 422
    assert c.post("/api/candidates", json=cand(3, backlog_count=-1), headers=H).status_code == 422
    r = c.post("/api/candidates", json=cand(4, percentage=50), headers=H); S["c_low"] = r.json()["candidate_id"]
    assert c.get("/api/candidates?name=Test User", headers=H).json()["total"] >= 2


def test_03_company_job():
    r = c.post("/api/companies", json={"company_name": "Test Co", "company_type": "STARTUP", "hr_email": "hr@test.co"}, headers=S["po"]); assert r.status_code == 201, r.text
    S["co"] = r.json()["company_id"]
    t = (date.today() + timedelta(days=10)).isoformat(); p = date.today().isoformat()
    job = {"job_code": f"JOB-TEST-{RUN}", "company_id": S["co"], "job_title": "Python Dev", "location": "Pune", "openings": 2, "qualifications": ["BE", "BTech"],
           "min_percentage": 60, "max_backlogs": 0, "required_technology": "Python", "posted_date": p, "application_deadline": t, "status": "OPEN"}
    assert c.post("/api/jobs", json={**job, "openings": 0}, headers=S["rec"]).status_code == 422
    assert c.post("/api/jobs", json={**job, "application_deadline": "2000-01-01"}, headers=S["rec"]).status_code == 422
    r = c.post("/api/jobs", json=job, headers=S["rec"]); assert r.status_code == 201, r.text
    S["job"] = r.json()["job_id"]; assert r.json()["skills"][0]["skill_name"] == "Python"
    assert c.post("/api/jobs", json=job, headers=S["rec"]).status_code == 409                               # duplicate job code


def test_04_eligibility_and_application():
    H = S["rec"]
    assert c.post("/api/applications/eligibility/check", json={"candidate_id": S["c1"], "job_id": S["job"]}, headers=H).json()["status"] == "ELIGIBLE"
    bad = c.post("/api/applications", json={"candidate_id": S["c_low"], "job_id": S["job"]}, headers=H)
    assert bad.status_code == 422 and "below required" in bad.json()["error"]["message"]
    r = c.post("/api/applications", json={"candidate_id": S["c1"], "job_id": S["job"], "source": "Portal"}, headers=H); assert r.status_code == 201, r.text
    S["app"] = r.json()["application_id"]
    assert c.post("/api/applications", json={"candidate_id": S["c1"], "job_id": S["job"]}, headers=H).status_code == 409   # duplicate application


def test_05_workflow_blocks_invalid_jumps():
    H, a = S["rec"], S["app"]
    assert c.patch(f"/api/applications/{a}/status", json={"status": "JOINED"}, headers=H).status_code == 409
    assert c.patch(f"/api/applications/{a}/status", json={"status": "SELECTED"}, headers=H).status_code == 409
    assert c.post("/api/offers", json={"application_id": a, "designation": "X", "offered_package_lpa": 5, "offer_date": date.today().isoformat()}, headers=S["po"]).status_code == 409
    assert c.patch(f"/api/applications/{a}/status", json={"status": "SHORTLISTED", "remarks": "ok"}, headers=H).status_code == 200


def test_06_interview_feedback_offer_placement():
    H, a = S["rec"], S["app"]
    today = date.today().isoformat()
    iv = {"application_id": a, "round_number": 1, "round_type": "TECHNICAL", "scheduled_date": today, "scheduled_time": "10:30", "mode": "ONLINE"}
    r = c.post("/api/interviews", json=iv, headers=H); assert r.status_code == 201, r.text
    i = r.json()["interview_id"]
    assert c.post("/api/interviews", json={**iv, "round_number": 2}, headers=H).status_code in (409,)          # earlier round still open
    assert c.post(f"/api/interviews/{i}/feedback", json={"technical_rating": 6, "recommendation": "SELECTED"}, headers=H).status_code == 422
    r = c.post(f"/api/interviews/{i}/feedback", json={"technical_rating": 4.5, "communication_rating": 4, "recommendation": "SELECTED", "remarks": "Strong"}, headers=H)
    assert r.status_code == 201, r.text
    assert c.get(f"/api/applications/{a}", headers=H).json()["application_status"] == "SELECTED"
    r = c.post("/api/offers", json={"application_id": a, "designation": "Python Developer", "offered_package_lpa": 6.5, "offer_date": today}, headers=S["po"]); assert r.status_code == 201, r.text
    o = r.json()["offer_id"]
    assert c.post(f"/api/offers/{o}/joining", json={"joining_status": "JOINED"}, headers=S["po"]).status_code == 409   # offer not accepted yet
    assert c.patch(f"/api/offers/{o}/status", json={"status": "ACCEPTED"}, headers=S["po"]).status_code == 200
    r = c.post(f"/api/offers/{o}/joining", json={"joining_status": "JOINED"}, headers=S["po"]); assert r.status_code == 200, r.text
    assert c.get(f"/api/candidates/{S['c1']}", headers=H).json()["placement_status"] == "PLACED"
    assert c.get(f"/api/applications/{a}", headers=H).json()["application_status"] == "JOINED"
    hist = [h["new_status"] for h in c.get(f"/api/applications/{a}/history", headers=H).json()]
    assert hist == ["APPLIED", "SHORTLISTED", "INTERVIEW_SCHEDULED", "INTERVIEWED", "SELECTED", "OFFERED", "JOINED"]


def test_07_transaction_rollback(monkeypatch):
    """If any step of the multi-table feedback operation fails, NOTHING is saved."""
    from rpms.service import interview_service as ivs
    H = S["rec"]
    r = c.post("/api/candidates", json=cand(5), headers=H); cid = r.json()["candidate_id"]
    a = c.post("/api/applications", json={"candidate_id": cid, "job_id": S["job"]}, headers=H).json()["application_id"]
    c.patch(f"/api/applications/{a}/status", json={"status": "SHORTLISTED"}, headers=H)
    i = c.post("/api/interviews", json={"application_id": a, "round_number": 1, "round_type": "HR", "scheduled_date": date.today().isoformat(), "mode": "OFFLINE"}, headers=H).json()["interview_id"]
    calls = {"n": 0}
    real = ivs.transition
    def flaky(*args, **kw):
        calls["n"] += 1
        if calls["n"] == 2: raise RuntimeError("simulated failure")
        return real(*args, **kw)
    monkeypatch.setattr(ivs, "transition", flaky)
    safe = TestClient(app, raise_server_exceptions=False)
    r = safe.post(f"/api/interviews/{i}/feedback", json={"recommendation": "SELECTED"}, headers=H)
    assert r.status_code == 500 and "simulated" not in r.text            # no internals leaked
    assert c.get(f"/api/interviews", headers=H).json()["items"][0] is not None
    with db.session() as cur:
        assert cur.one("SELECT COUNT(*) n FROM interview_feedback WHERE interview_id=%s", (i,))["n"] == 0
        assert cur.one("SELECT status FROM interview_rounds WHERE interview_id=%s", (i,))["status"] == "SCHEDULED"
        assert cur.one("SELECT application_status s FROM applications WHERE application_id=%s", (a,))["s"] == "INTERVIEW_SCHEDULED"


def test_08_reports_dashboard_logs_deactivate():
    H = S["admin"]
    d = c.get("/api/dashboard", headers=H).json(); assert d["kpis"]["total_candidates"] >= 20 and len(d["funnel"]) == 5
    rep = c.get("/api/reports", headers=H).json()
    assert len(rep) == 12 and all(k in rep for k in ("recruitment_funnel", "offer_to_joining", "job_aging", "unplaced_candidates"))
    assert c.get("/api/reports/nope", headers=H).status_code == 404
    assert len(c.get("/api/activity-logs", headers=H).json()) > 0
    assert c.get("/api/activity-logs", headers=S["rec"]).status_code == 403
    assert c.patch(f"/api/candidates/{S['c_low']}/deactivate", headers=S["rec"]).json()["profile_status"] == "INACTIVE"
    assert c.patch(f"/api/jobs/{S['job']}/close", headers=S["rec"]).json()["status"] == "CLOSED"
    assert c.get("/api/lookups", headers=H).json()["skills"]
