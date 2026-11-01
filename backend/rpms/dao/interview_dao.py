from .base import like, where

SEL = ("SELECT i.interview_id,i.application_id,a.application_code,ca.full_name AS candidate_name,c.company_name,j.job_title,i.round_number,"
       "i.round_type,i.scheduled_date,i.scheduled_time,i.mode,i.interviewer_name,i.meeting_or_location,i.status,"
       "(SELECT COUNT(*) FROM interview_feedback f WHERE f.interview_id=i.interview_id) AS has_feedback FROM interview_rounds i "
       "JOIN applications a ON a.application_id=i.application_id JOIN candidates ca ON ca.candidate_id=a.candidate_id "
       "JOIN jobs j ON j.job_id=a.job_id JOIN companies c ON c.company_id=j.company_id")


class InterviewDAO:
    @staticmethod
    def search(cur, f):
        w, p = where([("ca.full_name LIKE %s", like(f.get("candidate"))), ("c.company_id=%s", f.get("company_id")),
                      ("i.status=%s", f.get("status")), ("i.scheduled_date=%s", f.get("date")), ("i.application_id=%s", f.get("application_id"))])
        return cur.all(SEL + w + " ORDER BY i.scheduled_date DESC,i.scheduled_time DESC LIMIT 200", p)

    @staticmethod
    def find(cur, iid): return cur.one(SEL + " WHERE i.interview_id=%s", (iid,))

    @staticmethod
    def round_exists(cur, aid, n): return cur.one("SELECT 1 AS x FROM interview_rounds WHERE application_id=%s AND round_number=%s", (aid, n)) is not None

    @staticmethod
    def open_round(cur, aid):
        return cur.one("SELECT interview_id FROM interview_rounds WHERE application_id=%s AND status IN ('SCHEDULED','RESCHEDULED')", (aid,))

    @staticmethod
    def insert(cur, d):
        return cur.run("INSERT INTO interview_rounds (application_id,round_number,round_type,scheduled_date,scheduled_time,mode,interviewer_name,meeting_or_location) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (d["application_id"], d["round_number"], d["round_type"], d["scheduled_date"],
                                                           d.get("scheduled_time"), d["mode"], d.get("interviewer_name"), d.get("meeting_or_location")))

    @staticmethod
    def set_status(cur, iid, status): cur.run("UPDATE interview_rounds SET status=%s WHERE interview_id=%s", (status, iid))

    @staticmethod
    def reschedule(cur, iid, date, time):
        cur.run("UPDATE interview_rounds SET scheduled_date=%s,scheduled_time=%s,status='RESCHEDULED' WHERE interview_id=%s", (date, time, iid))

    @staticmethod
    def feedback_exists(cur, iid): return cur.one("SELECT 1 AS x FROM interview_feedback WHERE interview_id=%s", (iid,)) is not None

    @staticmethod
    def insert_feedback(cur, d):
        return cur.run("INSERT INTO interview_feedback (interview_id,technical_rating,communication_rating,problem_solving_rating,overall_rating,recommendation,remarks,submitted_by) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (d["interview_id"], d.get("technical_rating"), d.get("communication_rating"),
                                                           d.get("problem_solving_rating"), d.get("overall_rating"), d["recommendation"], d.get("remarks"), d["submitted_by"]))
