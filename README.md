# Webcam Painter

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/seyedeh-fatemeh-hosseininasab-7320bb322/)
[![GitHub](https://img.shields.io/badge/GitHub-fatemeh231-black?style=flat&logo=github)](https://github.com/fatemeh231)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

A real-time gesture-driven annotation tool that turns a webcam into a pen. Point your index finger at the screen and draw directly on multi-page PDFs, images, or blank pages — no stylus, no touchscreen, no mouse required.

![Demo](docs/demo.gif)

---

## Overview

Webcam Painter combines real-time hand landmark detection with a custom drawing canvas to enable natural, contact-free annotation. The system tracks the index fingertip as a cursor, interprets hand gestures to switch between drawing and moving, and composites strokes onto a transparent overlay above the loaded document.

The project is designed around three principles:

- **Real-time responsiveness** — the camera pipeline runs in a dedicated background thread so the UI never blocks.
- **Stable gesture detection** — a state machine with hysteresis and frame debouncing eliminates flicker that plagues naive threshold-based approaches.
- **Non-destructive annotation** — strokes live on a separate RGBA layer, preserving the original document until export.

---

## Features

- **Fingertip drawing** — the index fingertip functions as a pen with sub-pixel smoothing
- **Gesture-based state control** — index draws, index + middle moves, fist stops
- **Multi-page PDF support** — navigate pages, annotate any of them, drawings are preserved per page
- **Broad file support** — PDF, PNG, JPG, BMP, GIF, WebP, TIFF, plus placeholder previews for Word, Excel, PowerPoint, and Markdown
- **Zoom and pan** — toolbar buttons, mouse wheel, keyboard arrows, and reset control
- **Customizable pen** — 8 preset colors and 6 stroke thicknesses
- **Live camera preview** — hand landmarks and fingertip tracking displayed in real time
- **Debounced state machine** — hysteresis plus consecutive-frame confirmation to prevent state flicker

---

## Gesture Map

| Hand pose | State | Behavior |
|---|---|---|
| Index extended, middle curled | `DRAW` | Fingertip paints on the canvas |
| Index + middle extended | `MOVE` | Cursor follows finger, no stroke |
| All fingers curled (fist) | `IDLE` | Cursor hidden, no interaction |
| No hand detected | `IDLE` | Cursor hidden, no interaction |

The index finger is never required to change pose to start or stop drawing. This was a deliberate design decision: curling the index to "lift the pen" causes the cursor to jump and produces stroke noise. Instead, the middle finger acts as the pen up/down switch, keeping the index position stable throughout the gesture transition.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Hand tracking | MediaPipe Tasks — HandLandmarker |
| Camera and image operations | OpenCV |
| Canvas compositing | Pillow (RGBA overlay) |
| PDF rendering | PyMuPDF (fitz) |
| Desktop UI | CustomTkinter + Tkinter |
| Concurrency | Python `threading` with lock-protected shared state |

---

## Architecture

```
┌────────────┐   frames    ┌────────────────┐
│  Webcam    │────────────▶│  CameraThread  │
└────────────┘             │  (background)  │
                           └───────┬────────┘
                                   │  fingertip, finger ratios, state
                                   ▼
                           ┌────────────────┐
                           │  DrawState     │
                           │  (hysteresis + │
                           │   debounce)    │
                           └───────┬────────┘
                                   │  draw / move / idle
                                   ▼
┌────────────┐   polling   ┌────────────────┐
│  PainterApp│────────────▶│  CanvasView    │
│  (main UI) │  every 33ms │  base + overlay│
└────────────┘             └────────────────┘
```

The camera pipeline runs in a background daemon thread so the UI never blocks on `cv2.read()`. The main thread polls the latest state every ~33 ms and updates the canvas accordingly. All shared state is guarded by a `threading.Lock` to avoid race conditions between the camera and rendering threads.

---

## Installation

### Prerequisites

- Python 3.10 or newer
- A working webcam
- Windows, Linux, or macOS

### 1. Clone the repository

```bash
git clone https://github.com/fatemeh231/webcam-painter.git
cd webcam-painter
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the hand landmark model

The MediaPipe hand landmark model (~8 MB) is not stored in this repository. Download it once into the `models/` directory:

**Windows (Anaconda Prompt or CMD):**
```bash
mkdir models
curl -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

**PowerShell:**
```powershell
mkdir models
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "models\hand_landmarker.task"
```

**Linux / macOS:**
```bash
mkdir -p models
curl -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

---

## Usage

Run the application from the `src` directory:

```bash
cd src
python main.py
```

### Getting started

1. Click **Blank Page** to start from scratch, or **Upload File** to load a PDF or image.
2. Click **Cam: ON** to start the webcam.
3. Point your index finger at the camera. A cyan cursor appears on the canvas.
4. Keep only the index finger extended to draw.
5. Lift the middle finger to move the cursor without drawing.
6. Curl all fingers into a fist to stop — the cursor disappears.

### Keyboard shortcuts

| Key | Action |
|---|---|
| `←` `→` `↑` `↓` | Pan the document |
| `+` / `-` | Zoom in / out |
| `0` | Reset zoom and pan |
| `PageUp` / `PageDown` | Previous / next PDF page |
| Mouse wheel | Vertical pan |
| `Shift` + mouse wheel | Horizontal pan |

---

## Project Structure

```
webcam_painter/
├── models/
│   └── hand_landmarker.task          # downloaded separately
├── src/
│   ├── main.py                       # entry point
│   ├── app/
│   │   ├── window.py                 # main CustomTkinter window
│   │   ├── sidebar.py                # file upload and page navigation
│   │   ├── toolbar.py                # pen color, size, zoom, camera toggle
│   │   └── canvas_view.py            # base + overlay rendering, gestures
│   ├── vision/
│   │   ├── hand_tracker.py           # MediaPipe wrapper
│   │   └── camera_thread.py          # threaded webcam pipeline + DrawState
│   └── files/
│       └── file_loader.py            # PDF, image, and placeholder loading
├── data/
│   ├── uploads/                      # user files
│   └── output/
│       ├── drawings/                 # exported paint layers
│       └── annotated/                # exported annotated files
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Design Notes

**Why a background thread?** `cv2.read()` blocks. Running the camera loop on the main thread would freeze the UI between frames. Offloading it to a daemon thread keeps the interface responsive and lets the render loop run at its own cadence.

**Why hysteresis and debounce?** A naive threshold on a single hand measurement flickers when the value sits near the boundary. The state machine uses two thresholds (extended vs. curled with a dead zone between) plus a consecutive-frame counter before committing to a state change.

**Why the middle finger for pen up/down?** Early prototypes used the index finger itself as the drawing toggle, but curling it caused the fingertip position to jump and produced stray strokes. Moving the switch to the middle finger keeps the index position stable.

**Why an RGBA overlay?** Strokes are drawn on a transparent layer that composites over the base document. This preserves the original file until export and makes it trivial to clear, undo, or re-composite.

---

## Known Limitations

- **Pixel-based strokes** — annotations are rasterized onto an RGBA overlay rather than stored as vectors. Undo/redo and resolution-independent export are on the roadmap.
- **No pressure sensitivity** — stroke thickness is fixed per stroke.
- **Lighting dependent** — MediaPipe requires decent, front-facing illumination. Backlit scenes degrade tracking accuracy.
- **Frame-rate mismatch** — the camera thread and UI render loop run at different rates. Fingertip smoothing is applied to compensate.
- **Office formats** (`.docx`, `.xlsx`, `.pptx`, `.md`) currently show a placeholder card. Real preview rendering is planned.
- **Eager PDF loading** — all pages render up front. Very large documents (100+ pages) load slowly. Lazy loading is planned.

---


## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

## Author

**Seyedeh Fatemeh Hosseininasab**

- LinkedIn: [seyedeh-fatemeh-hosseininasab](https://www.linkedin.com/in/seyedeh-fatemeh-hosseininasab-7320bb322/)
- GitHub: [@fatemeh231](https://github.com/fatemeh231)
- Email: seyedehfatemehhosseininasab2@gmail.com