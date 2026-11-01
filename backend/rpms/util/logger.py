"""Activity logging: a simple text file (spec: File Handling) + the activity_logs table."""
import logging
from datetime import datetime
from .config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("mysql.connector").setLevel(logging.WARNING)
log = logging.getLogger("placepro.activity")


def log_activity(user_id, module, action, record_id, description):
    """Best-effort: a logging failure must never break a business operation."""
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} | user={user_id} | {module} | {action} | {record_id} | {description}"
    try:
        settings.LOG_FILE.parent.mkdir(exist_ok=True)
        with open(settings.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:
        log.warning("activity_log.txt not writable: %s", e)
    try:
        from .db import session
        with session() as cur:
            cur.run("INSERT INTO activity_logs (user_id,module_name,action_name,record_id,description) "
                    "VALUES (%s,%s,%s,%s,%s)", (user_id, module, action, str(record_id)[:60], str(description)[:500]))
    except Exception as e:  # noqa
        log.warning("activity_logs insert failed: %s", e)
