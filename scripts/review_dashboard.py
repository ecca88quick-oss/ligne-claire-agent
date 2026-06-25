#!/usr/bin/env python3
"""
review_dashboard.py
Step 2 + Step 4 – Review Dashboard with Queue Integration

Provides a CLI tool to:
  - List all queued items from the review queue (fed by image_similarity_flagger.py)
  - Approve, flag for revision, or block individual queue entries
  - Export a human-readable audit report
  - Show summary statistics

Shared log files:
  logs/review_queue.jsonl   <- written by image_similarity_flagger.py
  logs/audit_log.jsonl      <- final decisions written here

Usage:
    python review_dashboard.py list
    python review_dashboard.py review <id>
    python review_dashboard.py stats
    python review_dashboard.py export
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REVIEW_QUEUE = Path("logs/review_queue.jsonl")
AUDIT_LOG    = Path("logs/audit_log.jsonl")
EXPORT_HTML  = Path("logs/dashboard_export.html")

VALID_STATUSES = ("queued", "approved", "needs_revision", "blocked")

# ---------------------------------------------------------------------------
# JSONL helpers
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def save_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Queue helpers
# ---------------------------------------------------------------------------
def load_queue() -> list[dict]:
    return load_jsonl(REVIEW_QUEUE)


def save_queue(records: list[dict]) -> None:
    save_jsonl(REVIEW_QUEUE, records)


def find_by_id(records: list[dict], item_id: str) -> tuple[int, dict | None]:
    for i, rec in enumerate(records):
        if rec.get("id") == item_id:
            return i, rec
    return -1, None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_list(args) -> None:
    """List queue items, optionally filtered by status."""
    queue = load_queue()
    status_filter = getattr(args, "status", None)

    if status_filter:
        queue = [r for r in queue if r.get("status") == status_filter]

    if not queue:
        print("[INFO] No items in queue" + (f" with status '{status_filter}'" if status_filter else ""))
        return

    print(f"\n{'ID':36}  {'RISK':6}  {'STATUS':16}  {'SOURCE':28}  IMAGE")
    print("-" * 120)
    for rec in queue:
        print(
            f"{rec.get('id','?'):36}  "
            f"{rec.get('risk_level','?'):6}  "
            f"{rec.get('status','?'):16}  "
            f"{rec.get('source','?'):28}  "
            f"{Path(rec.get('generated_image','')).name}"
        )
    print(f"\nTotal: {len(queue)} item(s)")


def cmd_review(args) -> None:
    """Interactively review a single queue item."""
    queue = load_queue()
    idx, rec = find_by_id(queue, args.id)

    if rec is None:
        print(f"[ERROR] No item with id '{args.id}' found in queue.")
        sys.exit(1)

    print("\n=== Review Item ===")
    for k, v in rec.items():
        print(f"  {k:22}: {v}")

    print("\nDecision options:")
    print("  1) approved")
    print("  2) needs_revision")
    print("  3) blocked")
    print("  4) skip (keep as queued)")

    choice = input("\nEnter choice [1-4]: ").strip()
    decision_map = {"1": "approved", "2": "needs_revision", "3": "blocked", "4": None}
    decision = decision_map.get(choice)

    if decision is None:
        print("[INFO] Skipped. No changes made.")
        return

    notes = input("Reviewer notes (optional): ").strip()

    # Update queue entry
    queue[idx]["status"]         = decision
    queue[idx]["reviewer_notes"] = notes
    queue[idx]["reviewed_at"]    = datetime.now(timezone.utc).isoformat()
    save_queue(queue)

    # Append to audit log
    audit_entry = dict(queue[idx])
    audit_entry["decision"] = decision
    append_jsonl(AUDIT_LOG, audit_entry)

    print(f"[OK] Item {args.id[:8]}... -> {decision}")


def cmd_stats(args) -> None:
    """Print queue statistics."""
    queue = load_queue()
    audit = load_jsonl(AUDIT_LOG)

    status_counts: dict[str, int] = {}
    risk_counts:   dict[str, int] = {}
    for rec in queue:
        s = rec.get("status", "unknown")
        r = rec.get("risk_level", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
        risk_counts[r]   = risk_counts.get(r, 0) + 1

    print("\n=== Review Dashboard Statistics ===")
    print(f"  Queue entries : {len(queue)}")
    print(f"  Audit entries : {len(audit)}")
    print("\n  By Status:")
    for k, v in sorted(status_counts.items()):
        print(f"    {k:20}: {v}")
    print("\n  By Risk Level:")
    for k, v in sorted(risk_counts.items()):
        print(f"    {k:20}: {v}")


def cmd_export(args) -> None:
    """Export queue as a static HTML report."""
    queue = load_queue()
    rows  = ""
    for rec in queue:
        risk     = rec.get("risk_level", "")
        status   = rec.get("status", "")
        color    = {"HIGH": "#ff4444", "MEDIUM": "#ffaa00", "LOW": "#44bb44"}.get(risk, "#888")
        s_color  = {"approved": "#44bb44", "blocked": "#ff4444",
                    "needs_revision": "#ffaa00", "queued": "#aaa"}.get(status, "#aaa")
        rows += (
            f"<tr>"
            f"<td style='font-family:monospace;font-size:11px'>{rec.get('id','')[:8]}</td>"
            f"<td>{rec.get('timestamp','')[:19]}</td>"
            f"<td style='color:{color};font-weight:bold'>{risk}</td>"
            f"<td style='color:{s_color};font-weight:bold'>{status}</td>"
            f"<td>{Path(rec.get('generated_image','')).name}</td>"
            f"<td>{rec.get('closest_reference','')}</td>"
            f"<td>{rec.get('hamming_distance','')}</td>"
            f"<td>{rec.get('reviewer_notes','')}</td>"
            f"</tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang='en'>
<head><meta charset='UTF-8'>
<title>Ligne Claire Guardrail – Review Dashboard</title>
<style>
  body {{ font-family: sans-serif; background: #1a1a2e; color: #eee; padding: 2rem; }}
  h1   {{ color: #e94560; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th,td {{ border: 1px solid #333; padding: 6px 10px; text-align: left; }}
  th   {{ background: #16213e; color: #0f3460; color: #a8dadc; }}
  tr:nth-child(even) {{ background: #0f3460; }}
</style>
</head>
<body>
<h1>Ligne Claire Guardrail – Review Dashboard</h1>
<p>Generated: {datetime.now(timezone.utc).isoformat()} &nbsp;|&nbsp; Total items: {len(queue)}</p>
<table>
<thead><tr>
  <th>ID (short)</th><th>Timestamp</th><th>Risk</th><th>Status</th>
  <th>Generated Image</th><th>Closest Ref</th><th>Distance</th><th>Notes</th>
</tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body></html>
"""
    EXPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] HTML report exported to '{EXPORT_HTML}'")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Ligne Claire Guardrail – Review Dashboard (Step 2 + 4)"
    )
    sub = p.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List queue items")
    p_list.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")
    p_list.set_defaults(func=cmd_list)

    # review
    p_rev = sub.add_parser("review", help="Interactively review an item")
    p_rev.add_argument("id", help="Item UUID")
    p_rev.set_defaults(func=cmd_review)

    # stats
    p_stats = sub.add_parser("stats", help="Show queue statistics")
    p_stats.set_defaults(func=cmd_stats)

    # export
    p_exp = sub.add_parser("export", help="Export HTML report")
    p_exp.set_defaults(func=cmd_export)

    return p


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
