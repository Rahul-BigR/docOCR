"""ASGI entrypoint for the React app's backend.

The real DocOCR API lives in the project-root ``api.py`` Flask application.
This file used to contain temporary FastAPI mock routes, so running
``uvicorn backend.main:app`` returned fixed cheque data instead of executing
YOLO + TrOCR.  Keep this entrypoint, but mount the real Flask app so either
backend start command reaches the same OCR pipeline.
"""

from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api import app as flask_app, startup  # noqa: E402

startup()

app = FastAPI(title="DocOCR Backend")


@app.get("/")
def home():
    return {"message": "DocOCR Backend Running", "api": "Flask OCR pipeline"}


app.mount("/", WSGIMiddleware(flask_app))
