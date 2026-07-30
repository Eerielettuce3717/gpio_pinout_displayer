from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DETECT_DIR = ROOT / "runs" / "detect"
RUN_PREFIX = "yolov8n_edge"


def latest_run_dir() -> Path | None:
    runs: list[tuple[float, Path]] = []
    for run_dir in DETECT_DIR.glob(f"{RUN_PREFIX}*"):
        last_pt = run_dir / "weights" / "last.pt"
        if last_pt.is_file():
            runs.append((last_pt.stat().st_mtime, run_dir))
    if not runs:
        return None
    runs.sort(reverse=True)
    return runs[0][1]


def last_checkpoint() -> Path:
    run_dir = latest_run_dir()
    if run_dir is None:
        raise FileNotFoundError(f"no last.pt under {DETECT_DIR}/{RUN_PREFIX}*")
    return run_dir / "weights" / "last.pt"


def best_checkpoint() -> Path:
    run_dir = latest_run_dir()
    if run_dir is None:
        raise FileNotFoundError(f"no best.pt under {DETECT_DIR}/{RUN_PREFIX}*")
    best = run_dir / "weights" / "best.pt"
    if not best.is_file():
        raise FileNotFoundError(f"missing: {best}")
    return best
