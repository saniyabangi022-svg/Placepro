from .base import like, where

COLS = ["company_code", "company_name", "industry", "website", "location", "company_type", "hr_name", "hr_email", "hr_mobile", "status"]


class CompanyDAO:
    @staticmethod
    def search(cur, f):
        w, p = where([("c.company_name LIKE %s", like(f.get("name"))), ("c.industry LIKE %s", like(f.get("industry"))),
                      ("c.company_type=%s", f.get("company_type")), ("c.status=%s", f.get("status"))])
        return cur.all("SELECT c.*,(SELECT COUNT(*) FROM jobs j WHERE j.company_id=c.company_id AND j.status='OPEN') AS open_jobs "
                       "FROM companies c" + w + " ORDER BY c.company_id", p)

    @staticmethod
    def find(cur, cid): return cur.one("SELECT * FROM companies WHERE company_id=%s", (cid,))

    @staticmethod
    def insert(cur, d): return cur.run(f"INSERT INTO companies ({','.join(COLS)}) VALUES ({','.join(['%s'] * len(COLS))})", [d.get(c) for c in COLS])

    @staticmethod
    def update(cur, cid, d):
        cols = [c for c in COLS if c != "company_code"]
        cur.run(f"UPDATE companies SET {','.join(c + '=%s' for c in cols)} WHERE company_id=%s", [d.get(c) for c in cols] + [cid])

    @staticmethod
    def set_status(cur, cid, status): cur.run("UPDATE companies SET status=%s WHERE company_id=%s", (status, cid))
