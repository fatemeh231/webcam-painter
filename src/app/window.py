import os
import customtkinter as ctk

from app.sidebar import Sidebar
from app.toolbar import Toolbar
from app.canvas_view import CanvasView
from vision.camera_thread import CameraThread


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "hand_landmarker.task")


class PainterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Webcam Painter")
        self.geometry("1400x900")
        self.minsize(1100, 700)

        self.current_color = "#000000"
        self.current_thickness = 10
        self.loaded_file_path = None

        self.camera_thread = None
        self._camera_poll_id = None

        self._build_layout()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        right = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.toolbar = Toolbar(right, self)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

        self.canvas_view = CanvasView(right, self)
        self.canvas_view.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))

    def _bind_keys(self):
        self.bind("<Left>",  lambda e: self.canvas_view.pan_by(30, 0))
        self.bind("<Right>", lambda e: self.canvas_view.pan_by(-30, 0))
        self.bind("<Up>",    lambda e: self.canvas_view.pan_by(0, 30))
        self.bind("<Down>",  lambda e: self.canvas_view.pan_by(0, -30))
        self.bind("<plus>",  lambda e: self.canvas_view.zoom_by(1.15))
        self.bind("<equal>", lambda e: self.canvas_view.zoom_by(1.15))
        self.bind("<minus>", lambda e: self.canvas_view.zoom_by(1 / 1.15))
        self.bind("<Key-0>", lambda e: self.canvas_view.reset_view())

        self.bind("<Prior>", lambda e: self.canvas_view.prev_page())   # PageUp
        self.bind("<Next>",  lambda e: self.canvas_view.next_page())   # PageDown

    # ==================== camera ====================

    def toggle_camera(self):
        if self.camera_thread is None:
            self._start_camera()
        else:
            self._stop_camera()

    def _start_camera(self):
        print("Starting camera...")
        self.camera_thread = CameraThread(MODEL_PATH, camera_index=0)
        self.camera_thread.start()
        self.canvas_view.show_camera_panel()
        self._poll_camera()

    def _stop_camera(self):
        print("Stopping camera...")
        if self.camera_thread is not None:
            self.camera_thread.stop()
            self.camera_thread = None
        self.canvas_view.hide_camera_panel()

    def _poll_camera(self):
        if self.camera_thread is None:
            return
        state = self.camera_thread.get_state()
        if state["frame"] is not None:
            self.canvas_view.update_camera_frame(state["frame"])
        self.canvas_view.handle_camera_state(state)
        self._camera_poll_id = self.after(33, self._poll_camera)

    def _on_close(self):
        self._stop_camera()
        self.destroy()