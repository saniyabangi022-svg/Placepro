"""Small helpers shared by services."""
from ..exception.errors import ValidationFailedError


def blank_to_none(d: dict) -> dict:
    return {k: (None if isinstance(v, str) and not v.strip() else (v.strip() if isinstance(v, str) else v)) for k, v in d.items()}


def one_of(value, allowed, field):
    if value not in allowed:
        raise ValidationFailedError(f"{field} must be one of: {', '.join(allowed)}", {field: f"Choose a valid {field}."})
    return value
