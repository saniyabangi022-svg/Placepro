"""Authentication / authorization dependencies (JWT bearer token + role check)."""
from fastapi import Depends, Header

from ..exception.errors import AuthenticationError, PermissionDeniedError
from ..util.security import decode_token


def current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Please log in.")
    p = decode_token(authorization[7:])
    return {"user_id": int(p["sub"]), "name": p["name"], "role": p["role"]}


def require(*roles):
    def dep(user=Depends(current_user)):
        if user["role"] not in roles:
            raise PermissionDeniedError("Your role is not allowed to perform this action.")
        return user
    return dep


# Role policy (assumption - see README): reads are open to every logged-in user.
RECRUITING = require("ADMIN", "RECRUITER")                 # candidates, jobs, applications, interviews
PLACEMENT = require("ADMIN", "PLACEMENT_OFFICER")          # companies, offers, placements
ADMIN_ONLY = require("ADMIN")
