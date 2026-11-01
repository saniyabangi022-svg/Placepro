class OfferDAO:
    SEL = ("SELECT o.offer_id,o.offer_code,o.application_id,a.application_code,ca.full_name AS candidate_name,c.company_name,j.job_title,o.designation,"
           "o.offered_package_lpa,o.offer_date,o.expected_joining_date,o.offer_status,o.remarks,p.placement_id,p.joining_status,p.placement_status,p.actual_joining_date "
           "FROM offers o JOIN applications a ON a.application_id=o.application_id JOIN candidates ca ON ca.candidate_id=a.candidate_id "
           "JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id LEFT JOIN placements p ON p.offer_id=o.offer_id")

    @staticmethod
    def list(cur): return cur.all(OfferDAO.SEL + " ORDER BY o.offer_id DESC LIMIT 200")

    @staticmethod
    def find(cur, oid): return cur.one(OfferDAO.SEL + " WHERE o.offer_id=%s", (oid,))

    @staticmethod
    def find_by_application(cur, aid): return cur.one(OfferDAO.SEL + " WHERE o.application_id=%s", (aid,))

    @staticmethod
    def insert(cur, d):
        return cur.run("INSERT INTO offers (offer_code,application_id,designation,offered_package_lpa,offer_date,expected_joining_date,remarks) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                       (d["offer_code"], d["application_id"], d["designation"], d["offered_package_lpa"], d["offer_date"], d.get("expected_joining_date"), d.get("remarks")))

    @staticmethod
    def set_status(cur, oid, status, remarks):
        cur.run("UPDATE offers SET offer_status=%s,remarks=COALESCE(%s,remarks) WHERE offer_id=%s", (status, remarks, oid))

    @staticmethod
    def placement_for_offer(cur, oid): return cur.one("SELECT * FROM placements WHERE offer_id=%s", (oid,))

    @staticmethod
    def insert_placement(cur, d):
        return cur.run("INSERT INTO placements (candidate_id,company_id,job_id,offer_id,designation,final_package_lpa,expected_joining_date,actual_joining_date,joining_status,placement_status) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (d["candidate_id"], d["company_id"], d["job_id"], d["offer_id"], d["designation"], d["final_package_lpa"],
                                                                 d.get("expected_joining_date"), d.get("actual_joining_date"), d["joining_status"], d["placement_status"]))

    @staticmethod
    def update_placement(cur, pid, d):
        cur.run("UPDATE placements SET designation=%s,final_package_lpa=%s,actual_joining_date=%s,joining_status=%s,placement_status=%s WHERE placement_id=%s",
                (d["designation"], d["final_package_lpa"], d.get("actual_joining_date"), d["joining_status"], d["placement_status"], pid))

    @staticmethod
    def active_joined_count(cur, cid):
        return cur.one("SELECT COUNT(*) AS n FROM placements WHERE candidate_id=%s AND joining_status='JOINED' AND placement_status='ACTIVE'", (cid,))["n"]

    @staticmethod
    def placements(cur):
        return cur.all("SELECT p.placement_id,ca.full_name AS candidate_name,c.company_name,p.designation,p.final_package_lpa,p.actual_joining_date,p.joining_status,p.placement_status "
                       "FROM placements p JOIN candidates ca ON ca.candidate_id=p.candidate_id JOIN companies c ON c.company_id=p.company_id ORDER BY p.placement_id DESC LIMIT 200")
