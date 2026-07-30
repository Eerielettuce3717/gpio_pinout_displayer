# GPIO Pinout Displayer

- Webcam app that detects Raspberry Pi and Arduino boards with YOLOv8n
- Shows live ASCII GPIO pinout for whatever board is in frame

![GPIO Pinout Displayer — detection + pinout sidebar](https://via.placeholder.com/960x720?text=Add+screenshot+here)

## Why

I once spent way too long searching for the pinout for my Raspberry Pi 5 — scrolling down google and staring at whatever odd diagrams they had. That's my reason for creating this: point a camera at your microcontroller, and get the pinout on screen.

## The Algorithm

**Training (`train_detector.py`)**
- Fine-tunes YOLOv8n on `raspi_arduino_dataset` (20 board classes)
- Loads `yolov8n.pt`, trains 50 epochs at 640×640
- Saves `best.pt` / `last.pt` to `runs/detect/yolov8n_edge*/weights/`
- Exports ONNX for Jetson deployment

**Inference (`app.py`)**
- OpenCV captures webcam frames
- YOLO runs per-frame detection, highest-confidence box wins
- Class id → lookup in `pinouts.json` via `pinout_loader.py`
- Sidebar renders ASCII pinout (model name on first line)
- Detection held ~20 frames to cut flicker
- Auto-loads latest `best.pt` from `run_paths.py`

**Pinouts**
- `pinouts.json` — `ascii` + `ascii_detailed` per class
- Regen: `python scripts/generate_pinouts.py`

**Dependencies**
- `ultralytics`, `opencv-python`, `numpy`, `torch`

**Devices**
- Mac GPU: `--device mps`
- NVIDIA / Jetson: `--device 0`
- CPU: `--device cpu`

## Running this project

1. **Setup (once)**
   - `cd gpio_displayer`
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `python scripts/generate_pinouts.py`

2. **Train**
   - `python train_detector.py --device mps`
   - Resume: `python train_detector.py --resume --device mps`

3. **Run app**
   - activate venv every time: `source .venv/bin/activate`
   - Mac: `python app.py --source 0`
   - Linux / Jetson: `python app.py --source /dev/video0`
   - Mac camera: System Settings → Privacy & Security → Camera → enable Terminal or Cursor
   - `d` — pin details · `s` — snapshot · `q` — quit

[View a video explanation here](video link)