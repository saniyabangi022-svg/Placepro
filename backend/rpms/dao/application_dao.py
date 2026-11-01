from .base import like, paged, where

SEL = ("SELECT a.application_id,a.application_code,a.candidate_id,ca.full_name AS candidate_name,ca.candidate_code,a.job_id,j.job_code,"
       "j.job_title,c.company_id,c.company_name,a.eligibility_status,a.eligibility_reason,a.application_status,a.source,"
       "a.assigned_recruiter_id,u.full_name AS recruiter_name,a.applied_at FROM applications a "
       "JOIN candidates ca ON ca.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id "
       "LEFT JOIN users u ON u.user_id=a.assigned_recruiter_id")
CNT = "SELECT COUNT(*) AS n FROM applications a JOIN candidates ca ON ca.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id"


class ApplicationDAO:
    @staticmethod
    def search(cur, f, page=1, size=20):
        w, p = where([("a.application_code LIKE %s", like(f.get("application_code"))), ("ca.full_name LIKE %s", like(f.get("candidate"))),
                      ("c.company_id=%s", f.get("company_id")), ("j.job_code LIKE %s", like(f.get("job"))),
                      ("a.application_status=%s", f.get("status")), ("a.eligibility_status=%s", f.get("eligibility")),
                      ("DATE(a.applied_at)>=%s", f.get("date_from")), ("DATE(a.applied_at)<=%s", f.get("date_to")),
                      ("a.job_id=%s", f.get("job_id")), ("a.candidate_id=%s", f.get("candidate_id"))])
        r = paged(cur, SEL, CNT, w, p, "a.application_id DESC", page, size)
        r["pipeline"] = {x["application_status"]: x["n"] for x in cur.all("SELECT application_status,COUNT(*) AS n FROM applications GROUP BY application_status")}
        return r

    @staticmethod
    def find(cur, aid, lock=False):
        return cur.one(SEL + " WHERE a.application_id=%s" + (" FOR UPDATE" if lock else ""), (aid,)) if not lock else \
            cur.one("SELECT * FROM applications WHERE application_id=%s FOR UPDATE", (aid,))

    @staticmethod
    def exists(cur, candidate_id, job_id):
        return cur.one("SELECT application_id FROM applications WHERE candidate_id=%s AND job_id=%s", (candidate_id, job_id)) is not None

    @staticmethod
    def insert(cur, d):
        return cur.run("INSERT INTO applications (application_code,candidate_id,job_id,eligibility_status,eligibility_reason,application_status,source,assigned_recruiter_id) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (d["application_code"], d["candidate_id"], d["job_id"], d["eligibility_status"],
                                                           d["eligibility_reason"], d["application_status"], d.get("source"), d.get("assigned_recruiter_id")))

    @staticmethod
    def set_status(cur, aid, status): cur.run("UPDATE applications SET application_status=%s WHERE application_id=%s", (status, aid))

    @staticmethod
    def set_eligibility(cur, aid, status, reason):
        cur.run("UPDATE applications SET eligibility_status=%s,eligibility_reason=%s WHERE application_id=%s", (status, reason[:500], aid))

    @staticmethod
    def add_history(cur, aid, old, new, remarks, user_id):
        cur.run("INSERT INTO application_history (application_id,old_status,new_status,remarks,changed_by) VALUES (%s,%s,%s,%s,%s)",
                (aid, old, new, (remarks or "")[:500] or None, user_id))

    @staticmethod
    def history(cur, aid):
        return cur.all("SELECT h.history_id,h.old_status,h.new_status,h.remarks,u.full_name AS changed_by,h.changed_at FROM application_history h "
                       "JOIN users u ON u.user_id=h.changed_by WHERE h.application_id=%s ORDER BY h.history_id", (aid,))
