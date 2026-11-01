"""Reusable business validations. They raise ValidationFailedError with field-level messages."""
import re
from datetime import date
from ..exception.errors import ValidationFailedError

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE = re.compile(r"^\d{10}$")


def collect(errors: dict):
    if errors:
        raise ValidationFailedError("Please correct the highlighted fields.", errors)


def check_candidate(d: dict) -> None:
    e = {}
    if not (d.get("full_name") or "").strip(): e["full_name"] = "Please enter candidate name."
    if not EMAIL.match(d.get("email") or ""): e["email"] = "Enter a valid email address."
    if not MOBILE.match(d.get("mobile") or ""): e["mobile"] = "Mobile number must contain 10 digits."
    p = d.get("percentage")
    if p is None or not 0 <= float(p) <= 100: e["percentage"] = "Percentage must be between 0 and 100."
    if d.get("backlog_count") is None or int(d["backlog_count"]) < 0: e["backlog_count"] = "Backlog count cannot be negative."
    if not d.get("qualification"): e["qualification"] = "Qualification is required."
    if not d.get("passing_year"): e["passing_year"] = "Passing year is required."
    collect(e)


def check_job(d: dict) -> None:
    e = {}
    for k, m in (("job_code", "Job code is required."), ("job_title", "Job title is required."), ("location", "Location is required.")):
        if not (d.get(k) or "").strip(): e[k] = m
    if not d.get("openings") or int(d["openings"]) <= 0: e["openings"] = "Number of openings must be greater than zero."
    lo, hi = d.get("min_package_lpa"), d.get("max_package_lpa")
    if lo is not None and hi is not None and float(lo) > float(hi): e["max_package_lpa"] = "Minimum package must not exceed maximum package."
    mp = d.get("min_percentage")
    if mp is not None and not 0 <= float(mp) <= 100: e["min_percentage"] = "Percentage must be between 0 and 100."
    if d.get("max_backlogs") is not None and int(d["max_backlogs"]) < 0: e["max_backlogs"] = "Backlog count cannot be negative."
    y1, y2 = d.get("min_passing_year"), d.get("max_passing_year")
    if y1 and y2 and int(y1) > int(y2): e["max_passing_year"] = "Minimum passing year cannot exceed maximum passing year."
    try:
        if date.fromisoformat(str(d["application_deadline"])) < date.fromisoformat(str(d["posted_date"])):
            e["application_deadline"] = "Application deadline cannot be before posted date."
    except (KeyError, ValueError):
        e["application_deadline"] = "Valid posted date and deadline are required."
    collect(e)
