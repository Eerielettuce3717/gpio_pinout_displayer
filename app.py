#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from ultralytics import YOLO
except ImportError:
    sys.exit("need: pip install -r requirements.txt")

from pinout_loader import get_pinout_ascii
from run_paths import best_checkpoint

ROOT = Path(__file__).resolve().parent
FALLBACK_WEIGHTS = ROOT / "runs/detect/yolov8n_edge/weights/best.pt"
DEFAULT_CAMERA = 0 if sys.platform == "darwin" else "/dev/video0"

MONO_FONTS = (
    "/System/Library/Fonts/Menlo.ttc",
    "/Library/Fonts/Courier New.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)


def default_weights() -> Path:
    try:
        return best_checkpoint()
    except FileNotFoundError:
        return FALLBACK_WEIGHTS


VIDEO_W, VIDEO_H, SIDEBAR_W = 960, 720, 420
COLORS = {
    "text": (240, 240, 240),
    "muted": (160, 160, 160),
    "panel": (28, 28, 32),
    "header": (45, 45, 55),
    "highlight": (0, 220, 255),
    "ascii": (200, 210, 200),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--weights", type=Path, default=None)
    p.add_argument("--source", default=str(DEFAULT_CAMERA))
    p.add_argument("--conf", type=float, default=0.35)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--skip", type=int, default=1, help="run YOLO every N frames")
    return p.parse_args()


def infer_kwargs() -> dict:
    if sys.platform == "darwin":
        return {}
    return {"device": 0, "half": True}


def open_camera(source: str) -> cv2.VideoCapture:
    src: str | int = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        if sys.platform == "darwin":
            raise RuntimeError(
                "camera blocked — System Settings → Privacy & Security → Camera → "
                "enable Terminal (or Cursor/iTerm), then rerun"
            )
        raise RuntimeError(f"bad camera: {source}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def best_detection(result, conf_min: float) -> tuple[str, float] | None:
    if result.boxes is None or len(result.boxes) == 0:
        return None
    idx = int(result.boxes.conf.argmax())
    conf = float(result.boxes.conf[idx])
    if conf < conf_min:
        return None
    label = result.names[int(result.boxes.cls[idx])]
    return label, conf


def draw_boxes(frame: np.ndarray, result, conf_min: float) -> None:
    if result.boxes is None:
        return
    for box in result.boxes:
        conf = float(box.conf[0])
        if conf < conf_min:
            continue
        x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
        label = result.names[int(box.cls[0])]
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLORS["highlight"], 2)
        cv2.putText(
            frame,
            f"{label} {conf:.2f}",
            (x1, max(y1 - 8, 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            COLORS["highlight"],
            2,
            cv2.LINE_AA,
        )


def _mono_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in MONO_FONTS:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _rgb(bgr: tuple[int, int, int]) -> tuple[int, int, int]:
    return bgr[2], bgr[1], bgr[0]


def draw_ascii_block(sidebar: np.ndarray, lines: list[str], y_start: int) -> int:
    if not lines:
        return y_start

    margin_x = 4
    font_size = 10
    line_h = 15
    gap_h = 7
    font = _mono_font(font_size)
    max_len = max((len(line) for line in lines if line), default=0)
    padded = [line.ljust(max_len) if line else "" for line in lines]

    region_h = VIDEO_H - y_start - 4
    visible: list[str] = []
    used = 0
    for line in padded:
        h = gap_h if line == "" else line_h
        if used + h > region_h:
            break
        visible.append(line)
        used += h

    img_w = min(SIDEBAR_W - margin_x * 2, max(max_len * 6, 80))
    img_h = used
    img = Image.new("RGB", (img_w, img_h), _rgb(COLORS["panel"]))
    draw = ImageDraw.Draw(img)

    y = 0
    for i, line in enumerate(visible):
        if line == "":
            y += gap_h
            continue
        if i == 0:
            fill = _rgb(COLORS["highlight"])
        elif line.startswith("+") or line.startswith("|"):
            fill = _rgb(COLORS["ascii"])
        elif line.startswith(("Legend", "Power", "PWR", "       ")):
            fill = _rgb(COLORS["muted"])
        else:
            fill = _rgb(COLORS["text"])
        draw.text((0, y), line, font=font, fill=fill)
        y += line_h

    block = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    h, w = block.shape[:2]
    sidebar[y_start : y_start + h, margin_x : margin_x + w] = block
    return y_start + h


def draw_sidebar(
    sidebar: np.ndarray,
    board: str | None,
    conf: float | None,
    ascii_lines: list[str] | None,
    fps: float,
) -> None:
    sidebar[:] = COLORS["panel"]
    cv2.rectangle(sidebar, (0, 0), (SIDEBAR_W, 70), COLORS["header"], -1)
    cv2.putText(sidebar, "GPIO Pinout", (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS["text"], 2)
    cv2.putText(
        sidebar,
        f"FPS {fps:.1f} | d details | s snap | q quit",
        (16, 54),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        COLORS["muted"],
        1,
    )

    y = 82
    if not board:
        cv2.putText(sidebar, "No board detected", (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS["muted"], 2)
        return

    if conf is not None:
        cv2.putText(
            sidebar,
            f"Detected: {board} ({conf:.0%})",
            (16, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            COLORS["muted"],
            1,
        )
        y += 18

    if not ascii_lines:
        cv2.putText(sidebar, "Pinout unavailable", (16, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS["muted"], 1)
        return

    draw_ascii_block(sidebar, ascii_lines, y)


def main() -> None:
    args = parse_args()
    weights = (args.weights or default_weights()).expanduser().resolve()
    if not weights.is_file():
        sys.exit(f"missing weights: {weights}")

    captures = ROOT / "captures"
    captures.mkdir(exist_ok=True)

    model = YOLO(str(weights))
    cap = open_camera(args.source)
    ikw = infer_kwargs()

    board, conf = None, None
    hold = 0
    details = False
    fps, prev = 0.0, time.perf_counter()
    frame_i = 0
    last_result = None

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_i += 1
            if last_result is None or frame_i % args.skip == 0:
                last_result = model.predict(
                    frame, imgsz=args.imgsz, conf=args.conf, verbose=False, **ikw
                )[0]
            result = last_result
            video = frame.copy()
            draw_boxes(video, result, args.conf)

            hit = best_detection(result, args.conf)
            if hit:
                board, conf = hit
                hold = 0
            else:
                hold += 1
                if hold > 20:
                    board, conf = None, None

            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 / max(now - prev, 1e-6)
            prev = now

            ascii_lines = get_pinout_ascii(board, detailed=details) if board else None

            sidebar = np.zeros((VIDEO_H, SIDEBAR_W, 3), dtype=np.uint8)
            draw_sidebar(sidebar, board, conf, ascii_lines, fps)

            display = np.zeros((VIDEO_H, VIDEO_W + SIDEBAR_W, 3), dtype=np.uint8)
            display[:, :VIDEO_W] = cv2.resize(video, (VIDEO_W, VIDEO_H))
            display[:, VIDEO_W:] = sidebar

            cv2.imshow("GPIO Pinout Displayer", display)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("d"):
                details = not details
            if key == ord("s"):
                path = captures / f"snapshot_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                cv2.imwrite(str(path), display)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
