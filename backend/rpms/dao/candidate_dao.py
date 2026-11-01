from .base import like, paged, where

COLS = ["candidate_code", "full_name", "email", "mobile", "date_of_birth", "gender", "qualification", "college",
        "university", "passing_year", "percentage", "cgpa", "backlog_count", "primary_technology",
        "current_location", "preferred_location", "profile_status"]
LIST_SQL = ("SELECT candidate_id,candidate_code,full_name,email,mobile,qualification,passing_year,percentage,"
            "backlog_count,primary_technology,profile_status,placement_status FROM candidates")


class CandidateDAO:
    @staticmethod
    def search(cur, f, page=1, size=20):
        w, p = where([("candidate_code LIKE %s", like(f.get("candidate_code"))), ("full_name LIKE %s", like(f.get("name"))),
                      ("mobile LIKE %s", like(f.get("mobile"))), ("email LIKE %s", like(f.get("email"))),
                      ("primary_technology=%s", f.get("primary_technology")), ("passing_year=%s", f.get("passing_year")),
                      ("qualification=%s", f.get("qualification")), ("profile_status=%s", f.get("profile_status")),
                      ("placement_status=%s", f.get("placement_status"))])
        return paged(cur, LIST_SQL, "SELECT COUNT(*) AS n FROM candidates", w, p, "candidate_id DESC", page, size)

    @staticmethod
    def find(cur, cid): return cur.one("SELECT * FROM candidates WHERE candidate_id=%s", (cid,))

    @staticmethod
    def taken(cur, col, value, exclude_id=0):  # col is an internal constant ('email' / 'mobile')
        return cur.one(f"SELECT candidate_id FROM candidates WHERE {col}=%s AND candidate_id<>%s", (value, exclude_id)) is not None

    @staticmethod
    def insert(cur, d):
        return cur.run(f"INSERT INTO candidates ({','.join(COLS)}) VALUES ({','.join(['%s'] * len(COLS))})", [d.get(c) for c in COLS])

    @staticmethod
    def update(cur, cid, d):
        cols = [c for c in COLS if c != "candidate_code"]
        cur.run(f"UPDATE candidates SET {','.join(c + '=%s' for c in cols)} WHERE candidate_id=%s", [d.get(c) for c in cols] + [cid])

    @staticmethod
    def set_profile_status(cur, cid, status): cur.run("UPDATE candidates SET profile_status=%s WHERE candidate_id=%s", (status, cid))

    @staticmethod
    def set_placement_status(cur, cid, status): cur.run("UPDATE candidates SET placement_status=%s WHERE candidate_id=%s", (status, cid))

    @staticmethod
    def skills(cur, cid):
        return cur.all("SELECT s.skill_id,s.skill_name,cs.proficiency_level,cs.years_experience,cs.is_primary FROM candidate_skills cs "
                       "JOIN skills s ON s.skill_id=cs.skill_id WHERE cs.candidate_id=%s ORDER BY s.skill_name", (cid,))

    @staticmethod
    def replace_skills(cur, cid, items):
        cur.run("DELETE FROM candidate_skills WHERE candidate_id=%s", (cid,))
        for i in items:
            cur.run("INSERT INTO candidate_skills (candidate_id,skill_id,proficiency_level,years_experience,is_primary) VALUES (%s,%s,%s,%s,%s)",
                    (cid, i["skill_id"], i.get("proficiency_level"), i.get("years_experience") or 0, i.get("is_primary", 0)))

    @staticmethod
    def applications(cur, cid):
        return cur.all("SELECT a.application_id,a.application_code,j.job_code,j.job_title,c.company_name,a.eligibility_status,"
                       "a.application_status,a.applied_at FROM applications a JOIN jobs j ON j.job_id=a.job_id "
                       "JOIN companies c ON c.company_id=j.company_id WHERE a.candidate_id=%s ORDER BY a.applied_at DESC", (cid,))

    @staticmethod
    def interviews(cur, cid):
        return cur.all("SELECT i.interview_id,a.application_code,i.round_number,i.round_type,i.scheduled_date,i.scheduled_time,i.mode,i.status "
                       "FROM interview_rounds i JOIN applications a ON a.application_id=i.application_id WHERE a.candidate_id=%s "
                       "ORDER BY i.scheduled_date DESC", (cid,))

    @staticmethod
    def offers(cur, cid):
        return cur.all("SELECT o.offer_id,o.offer_code,o.designation,o.offered_package_lpa,o.offer_status,o.expected_joining_date,"
                       "p.joining_status,p.placement_status FROM offers o JOIN applications a ON a.application_id=o.application_id "
                       "LEFT JOIN placements p ON p.offer_id=o.offer_id WHERE a.candidate_id=%s", (cid,))
