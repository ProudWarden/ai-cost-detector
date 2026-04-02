# database.py
# SQLite database layer for the AI Cost Leak Detector.
# Uses only the Python standard library (sqlite3).

import sqlite3


def get_connection(db_path: str = "ai_costs.db") -> sqlite3.Connection:
    """
    Open and return a connection to the SQLite database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: An open database connection.
    """
    return sqlite3.connect(db_path)


def init_db(db_path: str = "ai_costs.db") -> None:
    """
    Initialise the database and create the ai_requests table if it
    does not already exist.

    Args:
        db_path (str): Path to the SQLite database file.
    """
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_requests (
                id            TEXT PRIMARY KEY,
                feature       TEXT,
                user_id       TEXT,
                model         TEXT,
                input_tokens  INTEGER,
                output_tokens INTEGER,
                cost          REAL,
                timestamp     TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def insert_request(
    request_id: str,
    feature: str,
    user_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    timestamp: str,
    db_path: str = "ai_costs.db",
) -> None:
    """
    Insert a single AI request record into the ai_requests table.

    Args:
        request_id (str):    Unique identifier for the request.
        feature (str):       Application feature that triggered the request.
        user_id (str):       Identifier of the user who made the request.
        model (str):         AI model used (e.g. 'gpt-4.1').
        input_tokens (int):  Number of prompt tokens consumed.
        output_tokens (int): Number of completion tokens generated.
        cost (float):        Total cost in USD.
        timestamp (str):     ISO-8601 timestamp of the request.
        db_path (str):       Path to the SQLite database file.

    Raises:
        sqlite3.IntegrityError: If a record with the same request_id already exists.
    """
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO ai_requests
                (id, feature, user_id, model, input_tokens, output_tokens, cost, timestamp)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (request_id, feature, user_id, model, input_tokens, output_tokens, cost, timestamp),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    DB = "ai_costs.db"

    # Initialise the database (creates the file and table if needed)
    init_db(DB)

    # Insert a sample request record
    insert_request(
        request_id="req-001",
        feature="summarisation",
        user_id="user-42",
        model="gpt-4.1-mini",
        input_tokens=1500,
        output_tokens=300,
        cost=0.001080,
        timestamp="2024-06-01T12:00:00Z",
        db_path=DB,
    )

    # Verify the record was written
    conn = get_connection(DB)
    row = conn.execute("SELECT * FROM ai_requests WHERE id = 'req-001'").fetchone()
    conn.close()

    print("Inserted record:", row)
