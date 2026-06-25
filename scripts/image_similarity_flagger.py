#!/usr/bin/env python3
"""
image_similarity_flagger.py
Step 3 – Heuristic Image Similarity Flagger

Compares generated images against a reference set of protected works
using perceptual hashing (aHash + dHash). Flags high/medium risk images
and automatically queues them in the Review Dashboard (review_queue.jsonl).

Usage:
    python image_similarity_flagger.py --generated path/to/image.png
    python image_similarity_flagger.py --batch path/to/generated_folder/

Dependencies:
    pip install Pillow imagehash
"""

import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    import imagehash
except ImportError:
    raise SystemExit("Missing dependencies. Run: pip install Pillow imagehash")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REFERENCE_DIR = Path("data/reference_images")   # protected / reference works
REVIEW_QUEUE  = Path("logs/review_queue.jsonl")  # shared with review_dashboard.py
SIMILARITY_LOG = Path("logs/similarity_log.jsonl")

# Hamming-distance thresholds (lower = more similar)
HIGH_RISK_THRESHOLD   = 8   # distance <= 8  -> HIGH risk
MEDIUM_RISK_THRESHOLD = 18  # distance <= 18 -> MEDIUM risk

HASH_SIZE = 16   # resolution for perceptual hash

# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------
def compute_hashes(img_path: Path):
    img = Image.open(img_path).convert("RGB")
    return {
        "ahash": imagehash.average_hash(img, hash_size=HASH_SIZE),
        "dhash": imagehash.dhash(img,        hash_size=HASH_SIZE),
    }


def min_distance(hashes_a: dict, hashes_b: dict) -> int:
    """Return the minimum Hamming distance across all hash combinations."""
    distances = [
        hashes_a["ahash"] - hashes_b["ahash"],
        hashes_a["dhash"] - hashes_b["dhash"],
    ]
    return min(distances)


# ---------------------------------------------------------------------------
# Reference index
# ---------------------------------------------------------------------------
def build_reference_index(ref_dir: Path) -> list[dict]:
    index = []
    if not ref_dir.exists():
        print(f"[WARN] Reference directory not found: {ref_dir}")
        print("       Create it and add reference images to enable similarity checks.")
        return index
    for img_path in sorted(ref_dir.iterdir()):
        if img_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            try:
                index.append({"path": img_path, "hashes": compute_hashes(img_path)})
            except Exception as exc:
                print(f"[WARN] Could not hash {img_path.name}: {exc}")
    print(f"[INFO] Reference index built: {len(index)} images from '{ref_dir}'")
    return index


# ---------------------------------------------------------------------------
# Core flag logic
# ---------------------------------------------------------------------------
def assess_risk(distance: int) -> str:
    if distance <= HIGH_RISK_THRESHOLD:
        return "HIGH"
    if distance <= MEDIUM_RISK_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def flag_image(generated_path: Path, reference_index: list[dict]) -> dict:
    """Compare one generated image against all reference images."""
    gen_hashes = compute_hashes(generated_path)
    best_distance = 9999
    best_ref      = None

    for ref in reference_index:
        dist = min_distance(gen_hashes, ref["hashes"])
        if dist < best_distance:
            best_distance = dist
            best_ref      = ref["path"].name

    risk_level = assess_risk(best_distance) if reference_index else "UNKNOWN"

    result = {
        "id":               str(uuid.uuid4()),
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "generated_image":  str(generated_path),
        "closest_reference": best_ref,
        "hamming_distance": best_distance,
        "risk_level":       risk_level,
    }
    return result


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def queue_for_review(result: dict) -> None:
    """Push HIGH / MEDIUM risk results to the shared review queue."""
    entry = {
        "id":              result["id"],
        "timestamp":       result["timestamp"],
        "source":          "image_similarity_flagger",
        "status":          "queued",
        "generated_image": result["generated_image"],
        "risk_level":      result["risk_level"],
        "closest_reference": result["closest_reference"],
        "hamming_distance":  result["hamming_distance"],
        "reviewer_notes":  "",
    }
    append_jsonl(REVIEW_QUEUE, entry)
    print(f"  -> Queued for human review  [{result['risk_level']}]  id={result['id']}")


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------
def process_image(img_path: Path, reference_index: list[dict]) -> dict:
    result = flag_image(img_path, reference_index)
    append_jsonl(SIMILARITY_LOG, result)

    label = result["risk_level"]
    dist  = result["hamming_distance"]
    ref   = result["closest_reference"] or "n/a"
    print(f"[{label:^7}] {img_path.name}  dist={dist}  closest_ref={ref}")

    if label in ("HIGH", "MEDIUM"):
        queue_for_review(result)

    return result


def run_batch(folder: Path, reference_index: list[dict]) -> list[dict]:
    results = []
    images  = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    )
    if not images:
        print(f"[WARN] No images found in '{folder}'")
        return results
    print(f"[INFO] Processing {len(images)} image(s) from '{folder}'")
    for img_path in images:
        results.append(process_image(img_path, reference_index))
    return results


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------
def print_summary(results: list[dict]) -> None:
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for r in results:
        counts[r["risk_level"]] = counts.get(r["risk_level"], 0) + 1
    print("\n=== Similarity Flagger Summary ===")
    for level, count in counts.items():
        print(f"  {level:8}: {count}")
    print(f"  TOTAL   : {len(results)}")
    queued = counts["HIGH"] + counts["MEDIUM"]
    if queued:
        print(f"  -> {queued} item(s) queued for review in '{REVIEW_QUEUE}'")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Heuristic image similarity flagger for Ligne Claire guardrail pipeline."
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--generated", type=Path, help="Path to a single generated image.")
    group.add_argument("--batch",     type=Path, help="Path to a folder of generated images.")
    p.add_argument(
        "--ref-dir", type=Path, default=REFERENCE_DIR,
        help=f"Reference image directory (default: {REFERENCE_DIR})"
    )
    return p


def main() -> None:
    args   = build_parser().parse_args()
    ref_index = build_reference_index(args.ref_dir)

    if args.generated:
        result  = process_image(args.generated, ref_index)
        results = [result]
    else:
        results = run_batch(args.batch, ref_index)

    print_summary(results)


if __name__ == "__main__":
    main()
