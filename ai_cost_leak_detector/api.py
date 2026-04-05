# api.py
# FastAPI layer for the AI Cost Leak Detector.
#
# Run with:
#   uvicorn ai_cost_leak_detector.api:app --reload

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_cost_leak_detector.tracker import track_request
from ai_cost_leak_detector.analytics import (
    get_total_cost,
    get_cost_by_feature,
    get_cost_by_user,
    get_recent_requests,
)
from ai_cost_leak_detector.insights import get_summary
from ai_cost_leak_detector.detector import (
    detect_high_cost_features,
    detect_high_cost_users,
    detect_large_requests,
    detect_concentration_risk,
)
from ai_cost_leak_detector.db.database import init_db

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Use /tmp for writable storage on hosted environments (e.g. Render).
# Override by setting the AI_COST_DB_PATH environment variable.
DB_PATH = os.environ.get("AI_COST_DB_PATH", "/tmp/ai_costs.db")

# Only these models are accepted
ALLOWED_MODELS = ["gpt-4.1-mini", "gpt-4.1"]


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the database and table exist before serving any requests
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
    # NOTE: cost is intentionally excluded — backend calculates it internally


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def rounded(value: float) -> float:
    """Round a cost value to 6 decimal places for clean responses."""
    return round(value, 6)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict:
    """Root endpoint — service health check."""
    return {
        "name":   "AI Cost Leak Detector",
        "status": "live",
        "docs":   "/docs",
    }


@app.post("/track")
def track(body: TrackRequest) -> dict:
    """
    Track a new AI request.
    Cost is calculated server-side from model + token counts.
    Returns request_id and calculated cost in USD.
    """
    # Validate model before doing anything else
    if body.model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{body.model}'. Allowed models: {ALLOWED_MODELS}",
        )

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
        "model":      body.model,
        "feature":    body.feature,
        "user_id":    body.user_id,
        "cost":       rounded(cost),
    }


@app.get("/analytics")
def analytics() -> dict:
    """
    Return total cost, cost grouped by feature, and cost grouped by user.
    """
    return {
        "total_cost": rounded(get_total_cost(DB_PATH)),
        "cost_by_feature": [
            {"feature": feature, "total_cost": rounded(cost)}
            for feature, cost in get_cost_by_feature(DB_PATH)
        ],
        "cost_by_user": [
            {"user_id": user_id, "total_cost": rounded(cost)}
            for user_id, cost in get_cost_by_user(DB_PATH)
        ],
    }


@app.get("/insights")
def insights() -> dict:
    """
    Return the insights summary: total cost, top feature, top user,
    and total request count.
    """
    summary = get_summary(DB_PATH)
    return {
        "total_cost":    rounded(summary["total_cost"]),
        "top_feature":   summary["top_feature"],
        "top_user":      summary["top_user"],
        "request_count": summary["request_count"],
    }


@app.get("/detect")
def detect() -> dict:
    """
    Run anomaly detection across all recorded requests.
    Returns leak_detected flag, severity, reason, and full detail.
    """
    high_cost_features = detect_high_cost_features(db_path=DB_PATH)
    high_cost_users    = detect_high_cost_users(db_path=DB_PATH)
    large_reqs         = detect_large_requests(db_path=DB_PATH)
    concentration      = detect_concentration_risk(db_path=DB_PATH)

    # Determine overall severity and reason
    issues = []

    if concentration:
        issues.append({"type": "concentration_risk", "severity": "high", "detail": concentration})

    for feature in high_cost_features:
        issues.append({
            "type":     "high_cost_feature",
            "severity": "medium",
            "detail":   f"Feature '{feature}' has exceeded the cost threshold.",
        })

    for user in high_cost_users:
        issues.append({
            "type":     "high_cost_user",
            "severity": "medium",
            "detail":   f"User '{user}' has exceeded the cost threshold.",
        })

    for row in large_reqs:
        issues.append({
            "type":     "large_request",
            "severity": "low",
            "detail":   f"Request '{row[0]}' used {row[4] + row[5]} tokens (feature: {row[1]}).",
        })

    # Overall severity: highest level found across all issues
    severity_rank = {"high": 3, "medium": 2, "low": 1}
    if issues:
        top_severity = max(issues, key=lambda x: severity_rank.get(x["severity"], 0))["severity"]
        leak_detected = True
        reason = f"{len(issues)} anomaly/anomalies detected."
    else:
        top_severity  = "none"
        leak_detected = False
        reason        = "No anomalies detected."

    return {
        "leak_detected": leak_detected,
        "severity":      top_severity,
        "reason":        reason,
        "issues":        issues,
    }
