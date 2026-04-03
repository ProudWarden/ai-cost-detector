# tracker.py
# Middleware layer for the AI Cost Leak Detector.
# Connects cost_engine (calculate_cost) and database (insert_request).

from ai_cost_leak_detector.core.cost_engine import calculate_cost
from ai_cost_leak_detector.db.database import insert_request


def track_request(
    request_id: str,
    feature: str,
    user_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    timestamp: str,
    db_path: str = "ai_costs.db",
) -> float:
    """
    Calculate the cost of an AI request and persist it to the database.

    Args:
        request_id (str):    Unique identifier for the request.
        feature (str):       Application feature that triggered the request.
        user_id (str):       Identifier of the user who made the request.
        model (str):         AI model used (e.g. 'gpt-4.1'). Must not be empty.
        input_tokens (int):  Number of prompt tokens consumed. Must be >= 0.
        output_tokens (int): Number of completion tokens generated. Must be >= 0.
        timestamp (str):     ISO-8601 timestamp of the request.
        db_path (str):       Path to the SQLite database file.

    Returns:
        float: The calculated cost in USD.

    Raises:
        ValueError: If model is empty or token counts are negative.
    """
    # Validate inputs
    if not model or not model.strip():
        raise ValueError("model must not be empty.")

    if input_tokens < 0:
        raise ValueError(f"input_tokens must be >= 0, got {input_tokens}.")

    if output_tokens < 0:
        raise ValueError(f"output_tokens must be >= 0, got {output_tokens}.")

    # Calculate cost via cost_engine
    cost = calculate_cost(model, input_tokens, output_tokens)

    # Persist the record via database layer
    insert_request(
        request_id=request_id,
        feature=feature,
        user_id=user_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
        timestamp=timestamp,
        db_path=db_path,
    )

    return cost


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cost = track_request(
        request_id="req-002",
        feature="summarisation",
        user_id="user-42",
        model="gpt-4.1-mini",
        input_tokens=1500,
        output_tokens=300,
        timestamp="2024-06-01T12:00:00Z",
    )

    print(f"Request tracked. Total cost: ${cost:.6f}")
