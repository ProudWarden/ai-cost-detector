# api.py
# FastAPI layer for the AI Cost Leak Detector.
#
# Run with:
#   uvicorn ai_cost_leak_detector.api:app --reload

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

from ai_cost_leak_detector.tracker import track_request
from ai_cost_leak_detector.analytics import (
    get_total_cost,
    get_cost_by_feature,
    get_cost_by_user,
)
from ai_cost_leak_detector.insights import get_summary
from ai_cost_leak_detector.detector import (
    detect_high_cost_features,
    detect_high_cost_users,
    detect_large_requests,
    detect_concentration_risk,
)
from ai_cost_leak_detector.db.database import init_db

# Use /tmp for writable storage on hosted environments (e.g. Render).
# Override by setting the AI_COST_DB_PATH environment variable.
DB_PATH = os.environ.get("AI_COST_DB_PATH", "/tmp/ai_costs.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise the database table on startup (safe to run multiple times).
    init_db(DB_PATH)
    yield


app = FastAPI(title="AI Cost Leak Detector", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class TrackRequest(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    feature: str
    user_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/track")
def track(body: TrackRequest) -> dict:
    """
    Track a new AI request.
    Returns the generated request_id and calculated cost in USD.
    """
    request_id = str(uuid.uuid4())
    timestamp  = datetime.now(timezone.utc).isoformat()

    cost = track_request(
        request_id=request_id,
        feature=body.feature,
        user_id=body.user_id,
        model=body.model,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        timestamp=timestamp,
        db_path=DB_PATH,
    )

    return {
        "request_id": request_id,
        "cost": cost,
    }


@app.get("/analytics")
def analytics() -> dict:
    """
    Return total cost, cost grouped by feature, and cost grouped by user.
    """
    return {
        "total_cost": get_total_cost(DB_PATH),
        "cost_by_feature": [
            {"feature": feature, "total_cost": cost}
            for feature, cost in get_cost_by_feature(DB_PATH)
        ],
        "cost_by_user": [
            {"user_id": user_id, "total_cost": cost}
            for user_id, cost in get_cost_by_user(DB_PATH)
        ],
    }


@app.get("/insights")
def insights() -> dict:
    """
    Return the insights summary: total cost, top feature, top user,
    and total request count.
    """
    return get_summary(DB_PATH)


@app.get("/detect")
def detect() -> dict:
    """
    Run all leak detection checks and return flagged results.
    """
    large_rows = detect_large_requests(db_path=DB_PATH)

    return {
        "high_cost_features": detect_high_cost_features(db_path=DB_PATH),
        "high_cost_users":    detect_high_cost_users(db_path=DB_PATH),
        "large_requests": [
            {
                "id":            row[0],
                "feature":       row[1],
                "user_id":       row[2],
                "model":         row[3],
                "input_tokens":  row[4],
                "output_tokens": row[5],
                "total_tokens":  row[4] + row[5],
                "cost":          row[6],
                "timestamp":     row[7],
            }
            for row in large_rows
        ],
        "concentration_risk": detect_concentration_risk(db_path=DB_PATH),
    }
