"""FastAPI application: API under /api, frontend pages served from the same origin."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from ..exception.errors import PlaceProError
from ..util import db
from ..util.config import settings
from .routers import core, workflow

log = logging.getLogger("placepro.api")
app = FastAPI(title="PlacePro API", version="1.0", description="Recruitment & Placement Management System backend")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


def _err(status, code, message, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details}})


@app.exception_handler(PlaceProError)
async def place_error(_: Request, e: PlaceProError): return _err(e.status_code, e.code, e.message, e.details)


@app.exception_handler(RequestValidationError)
async def bad_request(_: Request, e: RequestValidationError):
    fields = {".".join(str(x) for x in err["loc"][1:]): err["msg"] for err in e.errors()}
    return _err(422, "VALIDATION_FAILED", "Some fields are missing or have the wrong type.", fields)


@app.exception_handler(Exception)
async def unexpected(_: Request, e: Exception):
    log.exception("Unhandled error")                       # details go to the server log only
    return _err(500, "SERVER_ERROR", "Something went wrong on the server.")


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "database": "connected" if db.ping() else "down"}


for r in (core.auth, core.lookups, core.candidates, core.companies, core.jobs,
          workflow.applications, workflow.interviews, workflow.offers, workflow.reports, workflow.activity):
    app.include_router(r, prefix="/api")


@app.get("/", include_in_schema=False)
def home(): return RedirectResponse("/login.html")


if settings.FRONTEND_DIR.exists():                          # must be mounted last
    app.mount("/", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")
