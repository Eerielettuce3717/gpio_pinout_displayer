#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ultralytics import YOLO

from run_paths import best_checkpoint, last_checkpoint, latest_run_dir

ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / "raspi_arduino_dataset" / "data.yaml"
DATA_DIR = ROOT / "raspi_arduino_dataset"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--device", default="mps" if sys.platform == "darwin" else "cpu")
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def check_dataset() -> None:
    for split in ("train", "valid"):
        images = DATA_DIR / split / "images"
        if not images.is_dir():
            raise FileNotFoundError(f"missing: {images}")
        count = len(list(images.glob("*")))
        if count == 0:
            raise FileNotFoundError(f"empty: {images}")


def main() -> None:
    args = parse_args()

    if args.resume:
        ckpt = last_checkpoint()
        model = YOLO(str(ckpt))
        model.train(resume=True, device=args.device, batch=args.batch)
    else:
        if not DATA_YAML.is_file():
            raise FileNotFoundError(f"missing: {DATA_YAML}")
        check_dataset()
        model = YOLO("yolov8n.pt")
        model.train(
            data=str(DATA_YAML),
            epochs=args.epochs,
            imgsz=640,
            batch=args.batch,
            device=args.device,
            project=str(ROOT / "runs" / "detect"),
            name="yolov8n_edge",
            exist_ok=True,
            workers=2,
            amp=True,
            cache=False,
            patience=15,
        )

    best = best_checkpoint()
    YOLO(str(best)).export(format="onnx", imgsz=640, simplify=True, dynamic=False, opset=12)

    run = latest_run_dir()
    print(run)
    print(best)
    print(best.with_suffix(".onnx"))


if __name__ == "__main__":
    main()
