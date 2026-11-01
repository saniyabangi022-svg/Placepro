"""Candidate Eligibility Engine (pure logic, no database access -> easy to unit test).

Checks: candidate active, job open, deadline valid, not already applied, qualification, percentage,
passing year, backlogs, and mandatory job skills / technology (with minimum level).
Returns {"eligible": bool, "status": "ELIGIBLE"|"NOT_ELIGIBLE", "reasons": [...], "reason": str}.
"""
from datetime import date

LEVEL = {"BASIC": 1, "INTERMEDIATE": 2, "ADVANCED": 3}


def _qualification_ok(rule, qualification):
    if not rule:
        return True
    q = (qualification or "").strip().lower()
    for token in [t.strip().lower() for t in rule.replace(",", "/").split("/") if t.strip()]:
        if token.startswith("any") or q == token or q.startswith(token):
            return True
    return False


def check_eligibility(candidate, job, job_skills, candidate_skills, already_applied=False, today=None):
    today = today or date.today()
    why = []
    if candidate["profile_status"] != "ACTIVE":
        why.append(f"Candidate profile is {candidate['profile_status']}, not ACTIVE")
    if job["status"] != "OPEN":
        why.append(f"Job is {job['status']}, not OPEN")
    deadline = job["application_deadline"]
    if deadline and deadline < today:
        why.append(f"Application deadline {deadline} has passed")
    if already_applied:
        why.append("Candidate has already applied for this job")
    if not _qualification_ok(job.get("qualification_rule"), candidate.get("qualification")):
        why.append(f"Qualification {candidate.get('qualification')} does not match required ({job['qualification_rule']})")
    mp, pct = job.get("min_percentage"), candidate.get("percentage")
    if mp is not None and (pct is None or float(pct) < float(mp)):
        why.append(f"Percentage {pct if pct is not None else 'missing'} is below required {float(mp):g}")
    yr = candidate.get("passing_year")
    if job.get("min_passing_year") and yr < job["min_passing_year"]:
        why.append(f"Passing year {yr} is before {job['min_passing_year']}")
    if job.get("max_passing_year") and yr > job["max_passing_year"]:
        why.append(f"Passing year {yr} is after {job['max_passing_year']}")
    if candidate.get("backlog_count", 0) > (job.get("max_backlogs") or 0):
        why.append(f"Backlogs {candidate['backlog_count']} exceed allowed {job.get('max_backlogs') or 0}")
    have = {s["skill_name"].lower(): LEVEL.get((s.get("proficiency_level") or "").upper(), 0) for s in candidate_skills}
    prim = (candidate.get("primary_technology") or "").lower()
    for s in job_skills:
        if not s.get("mandatory_flag"):
            continue
        name = s["skill_name"].lower()
        if name not in have and not (prim and (name == prim or prim in name)):
            why.append(f"Missing mandatory skill {s['skill_name']}")
        elif name in have and LEVEL.get((s.get("minimum_level") or "").upper(), 0) > have[name] > 0:
            why.append(f"Skill {s['skill_name']} level is below required {s['minimum_level']}")
    ok = not why
    return {"eligible": ok, "status": "ELIGIBLE" if ok else "NOT_ELIGIBLE", "reasons": why,
            "reason": "Meets eligibility criteria" if ok else "; ".join(why)[:500]}
