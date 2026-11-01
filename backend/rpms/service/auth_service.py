from ..dao.lookup_dao import LookupDAO
from ..exception.errors import AuthenticationError
from ..util import security
from ..util.db import session
from ..util.logger import log_activity


def login(identity, password, role_code=None):
    with session() as cur:
        u = LookupDAO.user_for_login(cur, (identity or "").strip())
        # same generic message for every failure: never reveal which part was wrong
        if not u or u["status"] != "ACTIVE" or not security.verify_password(password or "", u["password_hash"]) \
                or (role_code and u["role_code"] != role_code):
            raise AuthenticationError("Invalid username, password or role.")
        LookupDAO.touch_login(cur, u["user_id"])
    log_activity(u["user_id"], "USER", "LOGIN", u["user_id"], f"{u['full_name']} logged in")
    return {"token": security.create_token(u), "user": {"user_id": u["user_id"], "full_name": u["full_name"], "role": u["role_code"]}}
