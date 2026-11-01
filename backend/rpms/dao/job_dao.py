from .base import like, paged, where

COLS = ["job_code", "company_id", "job_title", "employment_type", "location", "openings", "min_package_lpa", "max_package_lpa",
        "min_percentage", "min_passing_year", "max_passing_year", "max_backlogs", "experience_min_years", "qualification_rule",
        "posted_date", "application_deadline", "status", "created_by"]
SEL = ("SELECT j.job_id,j.job_code,j.company_id,c.company_name,j.job_title,j.employment_type,j.location,j.openings,j.min_package_lpa,"
       "j.max_package_lpa,j.status,j.posted_date,j.application_deadline,DATEDIFF(CURDATE(),j.posted_date) AS days_open FROM jobs j "
       "JOIN companies c ON c.company_id=j.company_id")


class JobDAO:
    @staticmethod
    def search(cur, f, page=1, size=20):
        w, p = where([("j.job_code LIKE %s", like(f.get("job_code"))), ("j.company_id=%s", f.get("company_id")),
                      ("j.location LIKE %s", like(f.get("location"))), ("j.status=%s", f.get("status")),
                      ("j.employment_type=%s", f.get("employment_type")),
                      ("EXISTS (SELECT 1 FROM job_skills js JOIN skills s ON s.skill_id=js.skill_id WHERE js.job_id=j.job_id AND s.skill_name=%s)", f.get("skill"))])
        return paged(cur, SEL, "SELECT COUNT(*) AS n FROM jobs j", w, p, "j.job_id DESC", page, size)

    @staticmethod
    def find(cur, jid):
        return cur.one("SELECT j.*,c.company_name,c.status AS company_status FROM jobs j JOIN companies c ON c.company_id=j.company_id WHERE j.job_id=%s", (jid,))

    @staticmethod
    def insert(cur, d): return cur.run(f"INSERT INTO jobs ({','.join(COLS)}) VALUES ({','.join(['%s'] * len(COLS))})", [d.get(c) for c in COLS])

    @staticmethod
    def update(cur, jid, d):
        cols = [c for c in COLS if c not in ("job_code", "created_by")]
        cur.run(f"UPDATE jobs SET {','.join(c + '=%s' for c in cols)} WHERE job_id=%s", [d.get(c) for c in cols] + [jid])

    @staticmethod
    def set_status(cur, jid, status): cur.run("UPDATE jobs SET status=%s WHERE job_id=%s", (status, jid))

    @staticmethod
    def skills(cur, jid):
        return cur.all("SELECT s.skill_id,s.skill_name,js.minimum_level,js.mandatory_flag FROM job_skills js "
                       "JOIN skills s ON s.skill_id=js.skill_id WHERE js.job_id=%s ORDER BY js.mandatory_flag DESC,s.skill_name", (jid,))

    @staticmethod
    def replace_skills(cur, jid, items):
        cur.run("DELETE FROM job_skills WHERE job_id=%s", (jid,))
        for i in items:
            cur.run("INSERT INTO job_skills (job_id,skill_id,minimum_level,mandatory_flag) VALUES (%s,%s,%s,%s)",
                    (jid, i["skill_id"], i.get("minimum_level"), i.get("mandatory_flag", 1)))
