"""Management reports (DB spec section 26) - joins, grouping, filtering and aggregates."""
from ..util.db import session

QUERIES = {
    "candidates_by_technology": "SELECT COALESCE(primary_technology,'Unspecified') AS label,COUNT(*) AS value FROM candidates GROUP BY primary_technology ORDER BY value DESC",
    "open_jobs_by_company": "SELECT c.company_name AS label,COUNT(*) AS value FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.status='OPEN' GROUP BY c.company_id,c.company_name ORDER BY value DESC",
    "applications_by_status": "SELECT application_status AS label,COUNT(*) AS value FROM applications GROUP BY application_status ORDER BY value DESC",
    "company_placements": "SELECT c.company_name AS label,COUNT(p.placement_id) AS value FROM placements p JOIN companies c ON c.company_id=p.company_id WHERE p.joining_status='JOINED' GROUP BY c.company_id,c.company_name ORDER BY value DESC",
    "technology_placements": "SELECT COALESCE(ca.primary_technology,'Unspecified') AS label,COUNT(*) AS value FROM placements p JOIN candidates ca ON ca.candidate_id=p.candidate_id WHERE p.joining_status='JOINED' GROUP BY ca.primary_technology ORDER BY value DESC",
    "recruiter_performance": ("SELECT u.full_name AS recruiter,COUNT(*) AS applications,SUM(a.application_status IN ('SELECTED','OFFERED','JOINED')) AS selected,"
                              "SUM(a.application_status='JOINED') AS joined FROM applications a JOIN users u ON u.user_id=a.assigned_recruiter_id GROUP BY u.user_id,u.full_name ORDER BY applications DESC"),
    "pending_interviews": ("SELECT i.interview_id,ca.full_name AS candidate,c.company_name AS company,i.scheduled_date,i.scheduled_time,i.status FROM interview_rounds i "
                           "JOIN applications a ON a.application_id=i.application_id JOIN candidates ca ON ca.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id "
                           "JOIN companies c ON c.company_id=j.company_id WHERE i.status='SCHEDULED' ORDER BY i.scheduled_date"),
    "job_aging": "SELECT job_code,job_title,posted_date,DATEDIFF(CURDATE(),posted_date) AS days_open FROM jobs WHERE status='OPEN' ORDER BY days_open DESC LIMIT 20",
    "placed_candidates": "SELECT candidate_code,full_name,primary_technology,placement_status FROM candidates WHERE placement_status='PLACED' ORDER BY full_name",
    "unplaced_candidates": "SELECT candidate_code,full_name,primary_technology,placement_status FROM candidates WHERE placement_status='NOT_PLACED' AND profile_status='ACTIVE' ORDER BY full_name LIMIT 100",
}


def run(name):
    with session() as cur:
        if name == "recruitment_funnel": return funnel(cur)
        if name == "offer_to_joining": return conversion(cur)
        return cur.all(QUERIES[name])


def funnel(cur):
    r = cur.one("SELECT COUNT(*) AS applied,SUM(application_status IN ('SHORTLISTED','INTERVIEW_SCHEDULED','INTERVIEWED','SELECTED','OFFERED','JOINED')) AS shortlisted,"
                "SUM(application_status IN ('INTERVIEWED','SELECTED','OFFERED','JOINED')) AS interviewed,SUM(application_status IN ('SELECTED','OFFERED','JOINED')) AS selected,"
                "SUM(application_status='JOINED') AS joined FROM applications")
    return [{"label": k.title(), "value": int(v or 0)} for k, v in r.items()]


def conversion(cur):
    r = cur.one("SELECT (SELECT COUNT(*) FROM offers) AS offers,(SELECT COUNT(*) FROM placements WHERE joining_status='JOINED') AS joined")
    return {"offers": r["offers"], "joined": r["joined"], "conversion_percent": round(100 * r["joined"] / r["offers"], 1) if r["offers"] else 0.0}


def all_reports():
    names = list(QUERIES) + ["recruitment_funnel", "offer_to_joining"]
    return {n: run(n) for n in names}


def dashboard():
    with session() as cur:
        k = cur.one("SELECT (SELECT COUNT(*) FROM candidates) AS total_candidates,(SELECT COUNT(*) FROM candidates WHERE profile_status='ACTIVE') AS active_candidates,"
                    "(SELECT COUNT(*) FROM companies WHERE status='ACTIVE') AS companies,(SELECT COUNT(*) FROM jobs WHERE status='OPEN') AS open_jobs,"
                    "(SELECT COUNT(*) FROM applications) AS applications,(SELECT COUNT(*) FROM interview_rounds) AS interviews,"
                    "(SELECT COUNT(*) FROM applications WHERE application_status IN ('SELECTED','OFFERED','JOINED')) AS selected,"
                    "(SELECT COUNT(*) FROM candidates WHERE placement_status='PLACED') AS placed,"
                    "(SELECT COUNT(*) FROM interview_rounds WHERE scheduled_date=CURDATE() AND status IN ('SCHEDULED','RESCHEDULED')) AS interviews_today")
        return {"kpis": k, "funnel": funnel(cur),
                "upcoming_interviews": cur.all("SELECT i.interview_id,ca.full_name AS candidate_name,c.company_name,i.round_type,i.scheduled_date,i.scheduled_time,i.mode,i.status FROM interview_rounds i "
                                               "JOIN applications a ON a.application_id=i.application_id JOIN candidates ca ON ca.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id "
                                               "JOIN companies c ON c.company_id=j.company_id WHERE i.status IN ('SCHEDULED','RESCHEDULED') ORDER BY i.scheduled_date,i.scheduled_time LIMIT 5"),
                "recent_jobs": cur.all("SELECT j.job_code,j.job_title,c.company_name,j.status FROM jobs j JOIN companies c ON c.company_id=j.company_id ORDER BY j.job_id DESC LIMIT 5"),
                "recent_placements": cur.all("SELECT ca.full_name AS candidate_name,c.company_name,p.final_package_lpa,p.joining_status FROM placements p JOIN candidates ca ON ca.candidate_id=p.candidate_id "
                                             "JOIN companies c ON c.company_id=p.company_id ORDER BY p.placement_id DESC LIMIT 5"),
                "recent_activity": cur.all("SELECT l.logged_at,u.full_name AS user_name,l.module_name,l.action_name,l.description FROM activity_logs l LEFT JOIN users u ON u.user_id=l.user_id ORDER BY l.log_id DESC LIMIT 5")}
