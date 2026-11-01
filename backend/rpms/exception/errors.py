"""Custom exceptions. Each carries an HTTP status so the API layer can map it automatically."""


class PlaceProError(Exception):
    status_code = 400
    code = "ERROR"

    def __init__(self, message="Request failed", details=None):
        super().__init__(message)
        self.message, self.details = message, details


class NotFoundError(PlaceProError):
    status_code, code = 404, "NOT_FOUND"


class CandidateNotFoundError(NotFoundError): code = "CANDIDATE_NOT_FOUND"
class CompanyNotFoundError(NotFoundError): code = "COMPANY_NOT_FOUND"
class JobNotFoundError(NotFoundError): code = "JOB_NOT_FOUND"
class ApplicationNotFoundError(NotFoundError): code = "APPLICATION_NOT_FOUND"
class InterviewNotFoundError(NotFoundError): code = "INTERVIEW_NOT_FOUND"
class OfferNotFoundError(NotFoundError): code = "OFFER_NOT_FOUND"


class DuplicateRecordError(PlaceProError):
    status_code, code = 409, "DUPLICATE_RECORD"


class DuplicateApplicationError(DuplicateRecordError):
    code = "DUPLICATE_APPLICATION"


class InvalidStatusTransitionError(PlaceProError):
    status_code, code = 409, "INVALID_STATUS_TRANSITION"


class CandidateNotEligibleError(PlaceProError):
    status_code, code = 422, "CANDIDATE_NOT_ELIGIBLE"


class ValidationFailedError(PlaceProError):
    status_code, code = 422, "VALIDATION_FAILED"


class AuthenticationError(PlaceProError):
    status_code, code = 401, "AUTHENTICATION_FAILED"


class PermissionDeniedError(PlaceProError):
    status_code, code = 403, "PERMISSION_DENIED"


class DatabaseError(PlaceProError):
    status_code, code = 500, "DATABASE_ERROR"
