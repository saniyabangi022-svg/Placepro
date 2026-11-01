"""Console menu (Python spec section 15).   python main.py
Uses the SAME service layer as the web API: Main -> Service -> DAO -> MySQL Connector -> MySQL."""
from rpms.exception.errors import PlaceProError
from rpms.reports import report_queries as rq
from rpms.service import (application_service as ap, auth_service, candidate_service as cs, company_service as co,
                          interview_service as iv, job_service as js, offer_service as of)

USER = {}


def ask(p, cast=str, default=None):
    v = input(f"  {p}{f' [{default}]' if default else ''}: ").strip() or (default or "")
    return cast(v) if v != "" else None


def show(rows, cols):
    if not rows: return print("  (no records)")
    print("  " + " | ".join(cols))
    for r in rows: print("  " + " | ".join(str(r.get(c, "")) for c in cols))


def menu(title, items):
    print(f"\n--- {title} ---")
    for i, t in enumerate(items, 1): print(f"  {i}. {t}")
    print("  0. Back")
    return input("Choose: ").strip()


def candidates():
    c = menu("Candidates", ["View all", "Search by name", "Add", "Deactivate"])
    if c == "1": show(cs.list_candidates({}, 1, 50)["items"], ["candidate_id", "candidate_code", "full_name", "primary_technology", "profile_status"])
    if c == "2": show(cs.list_candidates({"name": ask("Name")}, 1, 50)["items"], ["candidate_id", "candidate_code", "full_name", "email"])
    if c == "3":
        d = {k: ask(k.replace("_", " ")) for k in ("full_name", "email", "mobile", "qualification", "passing_year", "percentage", "backlog_count", "primary_technology")}
        d["passing_year"] = int(d["passing_year"] or 0); d["percentage"] = float(d["percentage"] or -1); d["backlog_count"] = int(d["backlog_count"] or 0)
        print("  Created:", cs.create_candidate(d, USER["user_id"])["candidate_code"])
    if c == "4": print(" ", cs.deactivate_candidate(ask("Candidate id", int), USER["user_id"]))


def companies():
    c = menu("Companies", ["View all", "Add"])
    if c == "1": show(co.list_companies({}), ["company_id", "company_code", "company_name", "location", "status", "open_jobs"])
    if c == "2": print("  Created:", co.create_company({"company_name": ask("Company name"), "industry": ask("Industry"), "location": ask("Location"), "company_type": ask("Type (MNC/STARTUP/MID_SIZE/CONSULTANCY)")}, USER["user_id"])["company_code"])


def jobs():
    c = menu("Jobs", ["View open jobs", "Close job"])
    if c == "1": show(js.list_jobs({"status": "OPEN"}, 1, 50)["items"], ["job_id", "job_code", "company_name", "job_title", "openings", "application_deadline"])
    if c == "2": print("  Job status:", js.close_job(ask("Job id", int), USER["user_id"])["status"])


def applications():
    c = menu("Applications", ["View all", "Check eligibility", "Apply", "Shortlist / Reject"])
    if c == "1": show(ap.list_applications({}, 1, 50)["items"], ["application_id", "application_code", "candidate_name", "job_code", "eligibility_status", "application_status"])
    if c == "2": r = ap.preview_eligibility(ask("Candidate id", int), ask("Job id", int)); print("  ", r["status"], "-", r["reason"])
    if c == "3": print("  Created:", ap.apply(ask("Candidate id", int), ask("Job id", int), "Internal", None, USER["user_id"])["application_code"])
    if c == "4": print("  Now:", ap.change_status(ask("Application id", int), ask("New status (SHORTLISTED/REJECTED)").upper(), ask("Remarks"), USER["user_id"])["application_status"])


def interviews():
    c = menu("Interviews", ["View all", "Schedule"])
    if c == "1": show(iv.list_interviews({})["items"], ["interview_id", "application_code", "candidate_name", "round_number", "round_type", "scheduled_date", "status"])
    if c == "2":
        d = {"application_id": ask("Application id", int), "round_number": ask("Round no", int, "1"), "round_type": ask("Type (APTITUDE/TECHNICAL/MANAGERIAL/HR)").upper(),
             "scheduled_date": ask("Date YYYY-MM-DD"), "mode": ask("Mode (ONLINE/OFFLINE/TELEPHONIC)").upper()}
        print("  Scheduled interview", iv.schedule(d, USER["user_id"])["interview_id"])


def offers():
    c = menu("Offers", ["View all", "Create", "Update status"])
    if c == "1": show(of.list_offers(), ["offer_id", "offer_code", "candidate_name", "designation", "offered_package_lpa", "offer_status"])
    if c == "2": print("  Created:", of.create_offer({"application_id": ask("Application id", int), "designation": ask("Designation"), "offered_package_lpa": ask("Package LPA", float), "offer_date": ask("Offer date YYYY-MM-DD")}, USER["user_id"])["offer_code"])
    if c == "3": print("  Now:", of.update_status(ask("Offer id", int), ask("Status (ACCEPTED/REJECTED/EXPIRED/WITHDRAWN)").upper(), None, USER["user_id"])["offer_status"])


def placements():
    c = menu("Placements", ["View all", "Confirm joining"])
    if c == "1": show(of.list_placements(), ["placement_id", "candidate_name", "company_name", "final_package_lpa", "joining_status"])
    if c == "2": print("  Joining:", of.confirm_joining(ask("Offer id", int), {"joining_status": ask("Status (JOINED/NOT_JOINED/DEFERRED/NO_SHOW/PENDING)").upper()}, USER["user_id"])["joining_status"])


def reports():
    names = list(rq.QUERIES) + ["recruitment_funnel", "offer_to_joining"]
    c = menu("Reports", names)
    if c.isdigit() and 0 < int(c) <= len(names):
        r = rq.run(names[int(c) - 1])
        show(r if isinstance(r, list) else [r], list(r[0].keys()) if isinstance(r, list) and r else list(r.keys()))


def main():
    print("=" * 34, "\nRECRUITMENT & PLACEMENT SYSTEM\n" + "=" * 34)
    try:
        d = auth_service.login(input("Username: "), input("Password: "))
    except PlaceProError as e:
        return print("Login failed:", e.message)
    USER.update(d["user"]); print("Welcome,", USER["full_name"])
    actions = {"1": candidates, "2": companies, "3": jobs, "4": applications, "5": interviews, "6": offers, "7": placements, "8": reports}
    while True:
        print("\n1. Candidates\n2. Companies\n3. Jobs\n4. Applications\n5. Interviews\n6. Offers\n7. Placements\n8. Reports\n9. Exit")
        ch = input("Choose: ").strip()
        if ch == "9": return print("Goodbye.")
        try:
            if ch in actions: actions[ch]()
            else: print("Invalid choice.")
        except PlaceProError as e: print("Error:", e.message, e.details or "")
        except (ValueError, TypeError): print("Error: please enter valid values.")


if __name__ == "__main__":
    main()
