# cli.py
# Command-line interface for the AI Cost Leak Detector.
#
# Example usage:
#   python3 -m ai_cost_leak_detector.cli --analytics
#   python3 -m ai_cost_leak_detector.cli --detect
#   python3 -m ai_cost_leak_detector.cli --insights
#   python3 -m ai_cost_leak_detector.cli --track \
#       --model gpt-4.1-mini --input_tokens 1500 --output_tokens 300 \
#       --feature summarisation --user_id user-42

import argparse
import uuid
from datetime import datetime, timezone

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


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_track(args: argparse.Namespace) -> None:
    """Track a new AI request and print the calculated cost."""
    request_id = str(uuid.uuid4())
    timestamp  = datetime.now(timezone.utc).isoformat()

    cost = track_request(
        request_id=request_id,
        feature=args.feature,
        user_id=args.user_id,
        model=args.model,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        timestamp=timestamp,
    )

    print(f"Request tracked.")
    print(f"  ID:            {request_id}")
    print(f"  Model:         {args.model}")
    print(f"  Feature:       {args.feature}")
    print(f"  User:          {args.user_id}")
    print(f"  Input tokens:  {args.input_tokens}")
    print(f"  Output tokens: {args.output_tokens}")
    print(f"  Cost:          ${cost:.6f}")


def cmd_analytics(args: argparse.Namespace) -> None:
    """Print total cost, cost by feature, and cost by user."""
    print("=== Analytics ===\n")

    total = get_total_cost(args.db)
    print(f"Total cost: ${total:.6f}\n")

    print("Cost by feature:")
    rows = get_cost_by_feature(args.db)
    if rows:
        for feature, cost in rows:
            print(f"  {feature:<30} ${cost:.6f}")
    else:
        print("  No data.")

    print("\nCost by user:")
    rows = get_cost_by_user(args.db)
    if rows:
        for user_id, cost in rows:
            print(f"  {user_id:<30} ${cost:.6f}")
    else:
        print("  No data.")


def cmd_insights(args: argparse.Namespace) -> None:
    """Print the summary from the insights layer."""
    summary = get_summary(args.db)

    print("=== Insights Summary ===\n")
    print(f"  Total cost:    ${summary['total_cost']:.6f}")
    print(f"  Top feature:   {summary['top_feature'] or 'N/A'}")
    print(f"  Top user:      {summary['top_user'] or 'N/A'}")
    print(f"  Request count: {summary['request_count']}")


def cmd_detect(args: argparse.Namespace) -> None:
    """Run all detection functions and print flagged results."""
    print("=== Leak Detection ===\n")

    print("High-cost features (threshold $0.001):")
    features = detect_high_cost_features(db_path=args.db)
    if features:
        for f in features:
            print(f"  [FLAGGED] {f}")
    else:
        print("  None flagged.")

    print("\nHigh-cost users (threshold $0.001):")
    users = detect_high_cost_users(db_path=args.db)
    if users:
        for u in users:
            print(f"  [FLAGGED] {u}")
    else:
        print("  None flagged.")

    print("\nLarge requests (>2000 tokens):")
    large = detect_large_requests(db_path=args.db)
    if large:
        for row in large:
            # row: (id, feature, user_id, model, input_tokens, output_tokens, cost, timestamp)
            total_tokens = row[4] + row[5]
            print(f"  [FLAGGED] id={row[0]}  tokens={total_tokens}  cost=${row[6]:.6f}  feature={row[1]}")
    else:
        print("  None flagged.")

    print("\nConcentration risk:")
    warning = detect_concentration_risk(args.db)
    print(f"  [WARNING] {warning}" if warning else "  No concentration risk detected.")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai_cost_leak_detector",
        description="AI Cost Leak Detector — CLI",
    )

    parser.add_argument(
        "--db",
        default="ai_costs.db",
        help="Path to the SQLite database file (default: ai_costs.db).",
    )

    # Mutually exclusive top-level commands
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--track",     action="store_true", help="Track a new AI request.")
    group.add_argument("--analytics", action="store_true", help="Print cost analytics.")
    group.add_argument("--insights",  action="store_true", help="Print insights summary.")
    group.add_argument("--detect",    action="store_true", help="Run leak detection.")

    # --track arguments
    parser.add_argument("--model",         type=str, help="Model name (required for --track).")
    parser.add_argument("--input_tokens",  type=int, help="Input token count (required for --track).")
    parser.add_argument("--output_tokens", type=int, help="Output token count (required for --track).")
    parser.add_argument("--feature",       type=str, help="Feature name (required for --track).")
    parser.add_argument("--user_id",       type=str, help="User ID (required for --track).")

    return parser


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    # Validate --track has all required sub-arguments
    if args.track:
        missing = [
            name for name, val in [
                ("--model",         args.model),
                ("--input_tokens",  args.input_tokens),
                ("--output_tokens", args.output_tokens),
                ("--feature",       args.feature),
                ("--user_id",       args.user_id),
            ]
            if val is None
        ]
        if missing:
            parser.error(f"--track requires: {', '.join(missing)}")
        cmd_track(args)

    elif args.analytics:
        cmd_analytics(args)

    elif args.insights:
        cmd_insights(args)

    elif args.detect:
        cmd_detect(args)


if __name__ == "__main__":
    main()
