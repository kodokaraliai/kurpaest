"""HTTP entry for the kurpaest.lt skeleton.

The ASGI app is a replaceable seam. Domain query/filter logic belongs in
modules that do not import FastAPI; this file only exposes a launchable
identity endpoint until those packages land.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

SERVICE_NAME = "kurpaest"
SERVICE_STATUS_OK = "ok"
SITE = "kurpaest.lt"

app = FastAPI(title="kurpaest.lt", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """Primary skeleton response: service identity and health."""
    return {
        "service": SERVICE_NAME,
        "status": SERVICE_STATUS_OK,
        "site": SITE,
    }
