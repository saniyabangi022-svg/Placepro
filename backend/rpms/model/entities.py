"""Model layer: plain data classes (spec: Model = data). Validation rules live in util.validators."""
from dataclasses import dataclass, asdict, field
from typing import Optional

from ..util import validators


@dataclass
class Candidate:
    full_name: str = ""
    email: str = ""
    mobile: str = ""
    qualification: str = ""
    passing_year: int = 0
    percentage: Optional[float] = None
    backlog_count: int = 0
    primary_technology: Optional[str] = None
    profile_status: str = "ACTIVE"
    placement_status: str = "NOT_PLACED"
    candidate_id: Optional[int] = None
    candidate_code: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    college: Optional[str] = None
    university: Optional[str] = None
    cgpa: Optional[float] = None
    current_location: Optional[str] = None
    preferred_location: Optional[str] = None

    def validate(self):
        validators.check_candidate(asdict(self))
        return self

    def to_dict(self): return asdict(self)


@dataclass
class Company:
    company_name: str = ""
    company_code: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    company_type: Optional[str] = None
    hr_name: Optional[str] = None
    hr_email: Optional[str] = None
    hr_mobile: Optional[str] = None
    status: str = "ACTIVE"

    def to_dict(self): return asdict(self)


@dataclass
class Job:
    job_code: str = ""
    company_id: int = 0
    job_title: str = ""
    location: str = ""
    openings: int = 1
    posted_date: str = ""
    application_deadline: str = ""
    employment_type: str = "FULL_TIME"
    min_package_lpa: Optional[float] = None
    max_package_lpa: Optional[float] = None
    min_percentage: Optional[float] = None
    min_passing_year: Optional[int] = None
    max_passing_year: Optional[int] = None
    max_backlogs: int = 0
    experience_min_years: float = 0
    qualification_rule: Optional[str] = None
    status: str = "OPEN"
    skills: list = field(default_factory=list)   # [{skill_name, minimum_level, mandatory_flag}]

    def validate(self):
        validators.check_job(asdict(self))
        return self

    def to_dict(self): return asdict(self)


@dataclass
class Application:
    candidate_id: int
    job_id: int
    source: Optional[str] = None
    assigned_recruiter_id: Optional[int] = None
    application_status: str = "APPLIED"
    eligibility_status: str = "PENDING"
    eligibility_reason: Optional[str] = None

    def to_dict(self): return asdict(self)


@dataclass
class InterviewRound:
    application_id: int
    round_number: int
    round_type: str
    scheduled_date: str
    mode: str
    scheduled_time: Optional[str] = None
    interviewer_name: Optional[str] = None
    meeting_or_location: Optional[str] = None
    status: str = "SCHEDULED"

    def to_dict(self): return asdict(self)


@dataclass
class Offer:
    application_id: int
    designation: str
    offered_package_lpa: float
    offer_date: str
    expected_joining_date: Optional[str] = None
    offer_status: str = "OFFERED"
    remarks: Optional[str] = None

    def to_dict(self): return asdict(self)


@dataclass
class Placement:
    offer_id: int
    designation: str
    final_package_lpa: float
    joining_status: str = "PENDING"
    placement_status: str = "ACTIVE"
    actual_joining_date: Optional[str] = None

    def to_dict(self): return asdict(self)
