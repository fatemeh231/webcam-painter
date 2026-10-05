import threading
import time

import cv2

from vision.hand_tracker import HandTracker


class DrawState:
    """
    index extended + middle curled  → DRAW
    index extended + middle extended → MOVE
    index curled (fist)              → IDLE (no cursor)
    """
    INDEX_EXTENDED = 0.75
    MIDDLE_EXTENDED = 0.75
    MIDDLE_CURLED = 0.55
    FRAMES_TO_START = 3

    def __init__(self):
        self.drawing = False
        self.cursor_active = False
        self._start_frames = 0

    def reset(self):
        self.drawing = False
        self.cursor_active = False
        self._start_frames = 0

    def update(self, index_ratio, middle_ratio):
        if index_ratio < self.INDEX_EXTENDED:
            self.drawing = False
            self.cursor_active = False
            self._start_frames = 0
            return self.drawing, self.cursor_active

        self.cursor_active = True

        if middle_ratio >= self.MIDDLE_EXTENDED:
            middle_up = True
        elif middle_ratio <= self.MIDDLE_CURLED:
            middle_up = False
        else:
            self._start_frames = 0
            return self.drawing, self.cursor_active

        if middle_up:
            self.drawing = False
            self._start_frames = 0
        else:
            if self.drawing:
                self._start_frames = 0
                return self.drawing, self.cursor_active
            self._start_frames += 1
            if self._start_frames >= self.FRAMES_TO_START:
                self.drawing = True
                self._start_frames = 0

        return self.drawing, self.cursor_active


class CameraThread(threading.Thread):
    def __init__(self, model_path, camera_index=0, width=640, height=480):
        super().__init__(daemon=True)
        self.model_path = model_path
        self.camera_index = camera_index
        self.width = width
        self.height = height

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        self.latest_frame_rgb = None
        self.fingertip_norm = None
        self.hand_present = False
        self.index_extended = False
        self.fps = 0.0

    def stop(self):
        self._stop_event.set()

    def get_state(self):
        with self._lock:
            return {
                "frame": self.latest_frame_rgb,
                "fingertip": self.fingertip_norm,
                "hand": self.hand_present,
                "index_extended": self.index_extended,
                "fps": self.fps,
            }

    def run(self):
        tracker = HandTracker(self.model_path, num_hands=1)
        draw_state = DrawState()

        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not cap.isOpened():
            print(f"[CameraThread] Could not open camera {self.camera_index}")
            return

        prev = time.time()
        fps = 0.0

        while not self._stop_event.is_set():
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands = tracker.process(rgb)

            h, w = frame.shape[:2]
            fingertip = None
            hand_present = False
            index_ratio = 0.0
            middle_ratio = 0.0

            if hands:
                hand_present = True
                hand0 = hands[0]

                for (x, y, _z) in hand0["landmarks"]:
                    cx, cy = int(x * w), int(y * h)
                    cv2.circle(rgb, (cx, cy), 3, (0, 200, 0), -1)

                index_ratio = hand0["index_length_ratio"]
                middle_ratio = hand0["middle_length_ratio"]
                drawing, cursor_active = draw_state.update(index_ratio, middle_ratio)

                ix, iy = hand0["index_tip"]
                cx, cy = int(ix * w), int(iy * h)

                if cursor_active:
                    fingertip = (ix, iy)

                if drawing:
                    dot_color = (0, 0, 255)
                elif cursor_active:
                    dot_color = (255, 255, 255)
                else:
                    dot_color = (120, 120, 120)
                cv2.circle(rgb, (cx, cy), 10, dot_color, -1)

                cv2.putText(
                    rgb, f"i={index_ratio:4.2f}  m={middle_ratio:4.2f}",
                    (cx + 15, cy - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1,
                )
            else:
                draw_state.reset()

            drawing = draw_state.drawing
            cursor_active = draw_state.cursor_active

            now = time.time()
            dt = now - prev
            prev = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            if drawing:
                label = "DRAW"
            elif cursor_active:
                label = "MOVE"
            else:
                label = "IDLE"

            cv2.putText(
                rgb, f"{fps:4.1f} FPS  {label}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2,
            )

            with self._lock:
                self.latest_frame_rgb = rgb
                self.fingertip_norm = fingertip
                self.hand_present = hand_present
                self.index_extended = drawing
                self.fps = fps

            time.sleep(0.005)

        cap.release()
        print("[CameraThread] stopped.")