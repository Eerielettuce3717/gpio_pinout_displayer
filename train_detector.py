#!/usr/bin/env python3
"""
Train a YOLOv8n detector and export to ONNX for Jetson Orin Nano deployment.

Requirements:
    pip install ultralytics

Dataset layout (data.yaml example):
    path: /path/to/dataset
    train: images/train
    val: images/val
    names:
      0: class_a
      1: class_b

Usage:
    # Train on Jetson Orin Nano (CUDA) or any machine with a GPU
    python train_detector.py --data /path/to/data.yaml

    # Override batch size if you hit GPU OOM on the Orin Nano
    python train_detector.py --data /path/to/data.yaml --batch 4

    # Train on CPU (slower; useful for smoke tests)
    python train_detector.py --data /path/to/data.yaml --device cpu

Outputs:
    runs/detect/<name>/weights/best.pt   - best PyTorch checkpoint
    runs/detect/<name>/weights/best.onnx - ONNX model for TensorRT / ONNX Runtime
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLOv8n and export ONNX for edge deployment."
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to Ultralytics dataset config (data.yaml).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Training epochs (default: 50).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Square input resolution (default: 640).",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=8,
        help="Batch size. Lower to 4 or 2 on Jetson if you run out of memory.",
    )
    parser.add_argument(
        "--device",
        default="0",
        help='CUDA device index ("0"), "cpu", or "mps" (default: "0").',
    )
    parser.add_argument(
        "--project",
        default="runs/detect",
        help='Training output directory root (default: "runs/detect").',
    )
    parser.add_argument(
        "--name",
        default="yolov8n_edge",
        help='Run name under project (default: "yolov8n_edge").',
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Dataloader workers. Keep low on Jetson to save RAM (default: 2).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data_yaml = args.data.expanduser().resolve()
    if not data_yaml.is_file():
        raise FileNotFoundError(f"Dataset config not found: {data_yaml}")

    # YOLOv8n: smallest variant, best latency/memory tradeoff on Orin Nano.
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        workers=args.workers,
        # Edge-oriented training settings
        amp=True,  # mixed precision: faster training, lower VRAM
        cache=False,  # avoid caching full dataset in RAM on memory-constrained boards
        patience=15,  # early stop if val metrics plateau
        save=True,
        plots=True,
        verbose=True,
    )

    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    export_model = YOLO(str(best_weights))

    # Static 640x640 ONNX simplifies TensorRT engine builds on Jetson.
    onnx_path = export_model.export(
        format="onnx",
        imgsz=args.imgsz,
        simplify=True,
        dynamic=False,
        opset=12,
        half=False,
    )

    print("\nTraining complete.")
    print(f"  Best weights : {best_weights}")
    print(f"  ONNX export  : {onnx_path}")
    print("\nNext step on Jetson: build a TensorRT engine from the ONNX file, e.g.")
    print(f"  trtexec --onnx={onnx_path} --saveEngine=yolov8n.engine --fp16")


if __name__ == "__main__":
    main()
