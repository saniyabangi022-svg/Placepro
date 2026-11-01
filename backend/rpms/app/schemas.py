"""Request bodies. Field-level business rules are enforced again in the service layer."""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class In(BaseModel):
    model_config = ConfigDict(extra="ignore")


class LoginIn(In):
    username: str
    password: str
    role: Optional[str] = None


class CandidateIn(In):
    full_name: str = ""
    email: str = ""
    mobile: str = ""
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    qualification: Optional[str] = None
    college: Optional[str] = None
    university: Optional[str] = None
    passing_year: Optional[int] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    backlog_count: Optional[int] = 0
    primary_technology: Optional[str] = None
    skills: List[str] = []
    skill_level: Optional[str] = None
    years_experience: Optional[float] = None
    current_location: Optional[str] = None
    preferred_location: Optional[str] = None
    profile_status: Optional[str] = "ACTIVE"


class CompanyIn(In):
    company_name: str = ""
    industry: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    company_type: Optional[str] = None
    hr_name: Optional[str] = None
    hr_email: Optional[str] = None
    hr_mobile: Optional[str] = None
    status: Optional[str] = "ACTIVE"


class StatusIn(In):
    status: str
    remarks: Optional[str] = None


class JobIn(In):
    job_code: str = ""
    company_id: Optional[int] = None
    job_title: str = ""
    employment_type: Optional[str] = "FULL_TIME"
    location: str = ""
    openings: Optional[int] = None
    min_package_lpa: Optional[float] = None
    max_package_lpa: Optional[float] = None
    qualifications: List[str] = []
    min_percentage: Optional[float] = None
    min_passing_year: Optional[int] = None
    max_passing_year: Optional[int] = None
    max_backlogs: Optional[int] = 0
    experience_min_years: Optional[float] = 0
    required_technology: Optional[str] = None
    required_skills: List[str] = []
    minimum_level: Optional[str] = None
    skill_type: Optional[str] = "Mandatory"
    posted_date: Optional[str] = None
    application_deadline: Optional[str] = None
    status: Optional[str] = "OPEN"


class ApplyIn(In):
    candidate_id: int
    job_id: int
    source: Optional[str] = None
    assigned_recruiter_id: Optional[int] = None


class EligibilityIn(In):
    candidate_id: int
    job_id: int


class InterviewIn(In):
    application_id: int
    round_number: int
    round_type: str
    scheduled_date: str
    scheduled_time: Optional[str] = None
    mode: str
    interviewer_name: Optional[str] = None
    meeting_or_location: Optional[str] = None


class RescheduleIn(In):
    scheduled_date: str
    scheduled_time: Optional[str] = None


class FeedbackIn(In):
    technical_rating: Optional[float] = None
    communication_rating: Optional[float] = None
    problem_solving_rating: Optional[float] = None
    overall_rating: Optional[float] = None
    recommendation: str
    remarks: Optional[str] = None


class OfferIn(In):
    application_id: int
    designation: str = ""
    offered_package_lpa: Optional[float] = None
    offer_date: Optional[str] = None
    expected_joining_date: Optional[str] = None
    remarks: Optional[str] = None


class JoiningIn(In):
    designation: Optional[str] = None
    final_package_lpa: Optional[float] = None
    actual_joining_date: Optional[str] = None
    joining_status: str
    placement_status: Optional[str] = "ACTIVE"
