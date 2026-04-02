# detector.py
# Leak detection layer for the AI Cost Leak Detector.
# Analyses existing data and flags potential cost issues.

from ai_cost_leak_detector.analytics import (
    get_cost_by_feature,
    get_cost_by_user,
    get_total_cost,
    get_recent_requests,
)
from ai_cost_leak_detector.insights import get_top_feature


def detect_high_cost_features(
    threshold: float = 0.001, db_path: str = "ai_costs.db"
) -> list[str]:
    """
    Return features whose total cost exceeds the threshold.

    Args:
        threshold (float): Minimum total cost in USD to flag.
        db_path (str):     Path to the SQLite database file.

    Returns:
        list[str]: Feature names where total cost > threshold.
    """
    return [
        feature
        for feature, total_cost in get_cost_by_feature(db_path)
        if total_cost > threshold
    ]


def detect_high_cost_users(
    threshold: float = 0.001, db_path: str = "ai_costs.db"
) -> list[str]:
    """
    Return users whose total cost exceeds the threshold.

    Args:
        threshold (float): Minimum total cost in USD to flag.
        db_path (str):     Path to the SQLite database file.

    Returns:
        list[str]: User IDs where total cost > threshold.
    """
    return [
        user_id
        for user_id, total_cost in get_cost_by_user(db_path)
        if total_cost > threshold
    ]


def detect_large_requests(
    token_threshold: int = 2000, db_path: str = "ai_costs.db"
) -> list[tuple]:
    """
    Return requests where combined token usage exceeds the threshold.

    Args:
        token_threshold (int): Maximum acceptable total tokens per request.
        db_path (str):         Path to the SQLite database file.

    Returns:
        list[tuple]: Full request rows where input_tokens + output_tokens
                     > token_threshold.
    """
    # Fetch all recorded requests (high limit to capture full history)
    all_requests = get_recent_requests(limit=10_000, db_path=db_path)

    # Row layout: (id, feature, user_id, model,
    #              input_tokens, output_tokens, cost, timestamp)
    return [
        row
        for row in all_requests
        if (row[4] + row[5]) > token_threshold  # input_tokens + output_tokens
    ]


def detect_concentration_risk(db_path: str = "ai_costs.db") -> str | None:
    """
    Warn if a single feature accounts for more than 70% of total cost.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        str | None: Warning message if concentration risk detected, else None.
    """
    total = get_total_cost(db_path)

    # No data or zero total — nothing to flag
    if not total:
        return None

    top_feature = get_top_feature(db_path)
    if top_feature is None:
        return None

    # Find the top feature's cost from the grouped results
    feature_rows = get_cost_by_feature(db_path)
    top_cost = next(
        (cost for feature, cost in feature_rows if feature == top_feature), 0.0
    )

    share = top_cost / total

    if share > 0.70:
        return (
            f"CONCENTRATION RISK: feature '{top_feature}' accounts for "
            f"{share:.1%} of total cost (${top_cost:.6f} / ${total:.6f})."
        )

    return None


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    DB = "ai_costs.db"

    print("=== High-cost features ===")
    for f in detect_high_cost_features(threshold=0.001, db_path=DB):
        print(f"  {f}")

    print("\n=== High-cost users ===")
    for u in detect_high_cost_users(threshold=0.001, db_path=DB):
        print(f"  {u}")

    print("\n=== Large requests (>2000 tokens) ===")
    for row in detect_large_requests(token_threshold=2000, db_path=DB):
        print(f"  {row}")

    print("\n=== Concentration risk ===")
    warning = detect_concentration_risk(DB)
    print(f"  {warning}" if warning else "  No concentration risk detected.")
