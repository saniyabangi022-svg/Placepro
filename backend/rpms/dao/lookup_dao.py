from .base import where


class LookupDAO:
    @staticmethod
    def lookups(cur):
        return {"skills": cur.all("SELECT skill_id,skill_name FROM skills WHERE is_active=1 ORDER BY skill_name"),
                "qualifications": cur.all("SELECT qualification_name FROM qualifications WHERE is_active=1 ORDER BY qualification_id"),
                "locations": cur.all("SELECT city_name FROM locations WHERE is_active=1 ORDER BY city_name"),
                "companies": cur.all("SELECT company_id,company_name FROM companies WHERE status='ACTIVE' ORDER BY company_name"),
                "recruiters": cur.all("SELECT u.user_id,u.full_name FROM users u JOIN roles r ON r.role_id=u.role_id WHERE r.role_code='RECRUITER' AND u.status='ACTIVE'"),
                "users": cur.all("SELECT user_id,full_name FROM users WHERE status='ACTIVE' ORDER BY full_name"),
                "candidates": cur.all("SELECT candidate_id,candidate_code,full_name FROM candidates WHERE profile_status='ACTIVE' ORDER BY full_name"),
                "jobs": cur.all("SELECT job_id,job_code,job_title FROM jobs WHERE status='OPEN' ORDER BY job_code"),
                "applications": cur.all("SELECT a.application_id,a.application_code,ca.full_name,j.job_code,a.application_status FROM applications a "
                                        "JOIN candidates ca ON ca.candidate_id=a.candidate_id JOIN jobs j ON j.job_id=a.job_id ORDER BY a.application_id DESC LIMIT 300")}

    @staticmethod
    def skill_map(cur): return {r["skill_name"].lower(): r["skill_id"] for r in cur.all("SELECT skill_id,skill_name FROM skills")}

    @staticmethod
    def user_for_login(cur, ident):
        return cur.one("SELECT u.user_id,u.username,u.password_hash,u.full_name,u.email,u.status,r.role_code FROM users u "
                       "JOIN roles r ON r.role_id=u.role_id WHERE u.username=%s OR u.email=%s", (ident, ident))

    @staticmethod
    def touch_login(cur, uid): cur.run("UPDATE users SET last_login_at=NOW() WHERE user_id=%s", (uid,))

    @staticmethod
    def activity(cur, f):
        w, p = where([("l.user_id=%s", f.get("user_id")), ("l.module_name=%s", f.get("module")), ("DATE(l.logged_at)=%s", f.get("date"))])
        return cur.all("SELECT l.log_id,u.full_name AS user_name,l.module_name,l.action_name,l.record_id,l.description,l.logged_at "
                       "FROM activity_logs l LEFT JOIN users u ON u.user_id=l.user_id" + w + " ORDER BY l.log_id DESC LIMIT 200", p)
