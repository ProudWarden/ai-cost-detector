# insights.py
# Insights layer for the AI Cost Leak Detector.
# Derives simple business insights from the analytics layer.

from ai_cost_leak_detector.analytics import (
    get_total_cost,
    get_cost_by_feature,
    get_cost_by_user,
)
from ai_cost_leak_detector.db.database import get_connection


def get_top_feature(db_path: str = "ai_costs.db") -> str | None:
    """
    Return the feature with the highest total cost.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        str | None: Feature name, or None if no data exists.
    """
    rows = get_cost_by_feature(db_path)
    # get_cost_by_feature returns rows ordered by cost DESC — first row is the top
    return rows[0][0] if rows else None


def get_top_user(db_path: str = "ai_costs.db") -> str | None:
    """
    Return the user_id with the highest total cost.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        str | None: User ID, or None if no data exists.
    """
    rows = get_cost_by_user(db_path)
    # get_cost_by_user returns rows ordered by cost DESC — first row is the top
    return rows[0][0] if rows else None


def get_summary(db_path: str = "ai_costs.db") -> dict:
    """
    Return a summary dictionary of key cost metrics.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        dict: {
            "total_cost"    (float): Sum of all request costs in USD,
            "top_feature"   (str | None): Feature with the highest total cost,
            "top_user"      (str | None): User with the highest total cost,
            "request_count" (int): Total number of recorded requests,
        }
    """
    # Direct COUNT query for an accurate total across all records
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM ai_requests").fetchone()
        request_count = int(row[0])
    finally:
        conn.close()

    return {
        "total_cost":    get_total_cost(db_path),
        "top_feature":   get_top_feature(db_path),
        "top_user":      get_top_user(db_path),
        "request_count": request_count,
    }


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    summary = get_summary()

    print("=== AI Cost Leak Detector — Summary ===")
    print(f"  Total cost:    ${summary['total_cost']:.6f}")
    print(f"  Top feature:   {summary['top_feature']}")
    print(f"  Top user:      {summary['top_user']}")
    print(f"  Request count: {summary['request_count']}")
