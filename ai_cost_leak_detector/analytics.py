# analytics.py
# Analytics and reporting layer for the AI Cost Leak Detector.
# Reads from the ai_requests table in SQLite.

from ai_cost_leak_detector.db.database import get_connection


def get_total_cost(db_path: str = "ai_costs.db") -> float:
    """
    Return the total cost of all records in the database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        float: Sum of all costs in USD. Returns 0.0 if no records exist.
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT COALESCE(SUM(cost), 0.0) FROM ai_requests").fetchone()
        return float(row[0])
    finally:
        conn.close()


def get_cost_by_feature(db_path: str = "ai_costs.db") -> list[tuple]:
    """
    Return total cost grouped by feature, descending by cost.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        list[tuple]: Each tuple is (feature, total_cost).
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute("""
            SELECT feature, SUM(cost) AS total_cost
            FROM ai_requests
            GROUP BY feature
            ORDER BY total_cost DESC
        """).fetchall()
        return rows
    finally:
        conn.close()


def get_cost_by_user(db_path: str = "ai_costs.db") -> list[tuple]:
    """
    Return total cost grouped by user_id, descending by cost.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        list[tuple]: Each tuple is (user_id, total_cost).
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute("""
            SELECT user_id, SUM(cost) AS total_cost
            FROM ai_requests
            GROUP BY user_id
            ORDER BY total_cost DESC
        """).fetchall()
        return rows
    finally:
        conn.close()


def get_recent_requests(limit: int = 10, db_path: str = "ai_costs.db") -> list[tuple]:
    """
    Return the most recent requests ordered by timestamp descending.

    Args:
        limit (int):   Maximum number of rows to return.
        db_path (str): Path to the SQLite database file.

    Returns:
        list[tuple]: Each tuple is a full ai_requests row:
                     (id, feature, user_id, model, input_tokens,
                      output_tokens, cost, timestamp)
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute("""
            SELECT id, feature, user_id, model,
                   input_tokens, output_tokens, cost, timestamp
            FROM ai_requests
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return rows
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    DB = "ai_costs.db"

    total = get_total_cost(DB)
    print(f"Total cost: ${total:.6f}\n")

    print("Cost by feature:")
    for feature, cost in get_cost_by_feature(DB):
        print(f"  {feature}: ${cost:.6f}")

    print("\nCost by user:")
    for user_id, cost in get_cost_by_user(DB):
        print(f"  {user_id}: ${cost:.6f}")

    print("\nRecent requests:")
    for row in get_recent_requests(limit=10, db_path=DB):
        print(f"  {row}")
