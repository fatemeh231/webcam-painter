import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk


MIN_ZOOM = 0.25
MAX_ZOOM = 5.0


class CanvasView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=10)
        self.app = app

        # pages
        self._pages = []
        self._overlays = []
        self._overlay_draws = []
        self._current_page = 0
        self._has_page = False

        # display
        self._photo = None
        self._offset_x = 0
        self._offset_y = 0

        # zoom & pan
        self._zoom = 1.0
        self._pan_x = 0
        self._pan_y = 0

        # finger state
        self._finger_smooth = None
        self._finger_last_pt = None
        self._cursor_img_pos = None

        # mouse drawing
        self._drawing = False
        self._last_pt = None

        # camera panel
        self._camera_label = None
        self._camera_photo = None

        self.canvas = tk.Canvas(
            self, bg="#1e1e1e", highlightthickness=0, cursor="pencil"
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Configure>", lambda e: self._render())
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        self._show_welcome()

    # ==================== camera panel ====================

    def show_camera_panel(self):
        if self._camera_label is not None:
            return
        self._camera_label = tk.Label(
            self, bg="black",
            bd=0, highlightthickness=2, highlightbackground="#1e88e5",
        )
        self._camera_label.place(relx=0.98, rely=0.03, anchor="ne",
                                 width=260, height=195)

    def hide_camera_panel(self):
        if self._camera_label is not None:
            self._camera_label.destroy()
            self._camera_label = None
            self._camera_photo = None
        self.canvas.delete("finger_cursor")
        self._cursor_img_pos = None
        self._finger_last_pt = None
        self._finger_smooth = None

    def update_camera_frame(self, rgb_array):
        if self._camera_label is None:
            return
        pil = Image.fromarray(rgb_array)
        pil = pil.resize((260, 195), Image.BILINEAR)
        self._camera_photo = ImageTk.PhotoImage(pil)
        self._camera_label.configure(image=self._camera_photo)

    # ==================== gesture dispatch ====================

    def handle_camera_state(self, state):
        drawing = state.get("hand") and state.get("index_extended")
        fingertip = state.get("fingertip")

        if drawing and fingertip is not None:
            self._handle_draw(fingertip)
        else:
            self._handle_idle(fingertip)

    def _handle_draw(self, fingertip):
        self.canvas.delete("finger_cursor")
        if fingertip is None or not self._pages:
            self._finger_last_pt = None
            self._cursor_img_pos = None
            return

        ix, iy = self._smooth_to_image(fingertip)
        self._cursor_img_pos = (ix, iy)

        if self._finger_last_pt is not None:
            self._draw_segment(self._finger_last_pt, (ix, iy))
        self._finger_last_pt = (ix, iy)
        self._render()

    def _handle_idle(self, fingertip):
        self._finger_last_pt = None
        self.canvas.delete("finger_cursor")

        if fingertip is None or not self._pages:
            self._finger_smooth = None
            self._cursor_img_pos = None
            return

        ix, iy = self._smooth_to_image(fingertip)
        self._cursor_img_pos = (ix, iy)
        self._draw_cursor_only(ix, iy, color="#00e5ff")

    # ==================== coordinate helpers ====================

    def _smooth_to_image(self, fingertip_norm):
        nx, ny = fingertip_norm
        if self._finger_smooth is None:
            self._finger_smooth = [nx, ny]
        else:
            a = 0.5
            self._finger_smooth[0] = a * nx + (1 - a) * self._finger_smooth[0]
            self._finger_smooth[1] = a * ny + (1 - a) * self._finger_smooth[1]

        w, h = self._pages[self._current_page].size
        ix = int(self._finger_smooth[0] * w)
        iy = int(self._finger_smooth[1] * h)
        ix = max(0, min(ix, w - 1))
        iy = max(0, min(iy, h - 1))
        return ix, iy

    def _to_image_coords(self, event):
        ix = (event.x - self._offset_x) / self._zoom
        iy = (event.y - self._offset_y) / self._zoom
        return int(ix), int(iy)

    def _in_bounds(self, x, y):
        if not self._pages:
            return False
        w, h = self._pages[self._current_page].size
        return 0 <= x < w and 0 <= y < h

    # ==================== zoom / pan API ====================

    def zoom_by(self, factor):
        new_zoom = self._zoom * factor
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))
        if abs(new_zoom - self._zoom) < 1e-4:
            return
        self._zoom = new_zoom
        self._render()
        self.app.toolbar.update_zoom_label(self._zoom)

    def reset_view(self):
        self._zoom = 1.0
        self._pan_x = 0
        self._pan_y = 0
        self._render()
        self.app.toolbar.update_zoom_label(self._zoom)

    def pan_by(self, dx, dy):
        self._pan_x += dx
        self._pan_y += dy
        self._render()

    def _on_mousewheel(self, event):
        shift = bool(event.state & 0x0001)
        if shift:
            self.pan_by(event.delta // 2, 0)
        else:
            self.pan_by(0, event.delta // 2)

    # ==================== page navigation ====================

    def next_page(self):
        if not self._pages or self._current_page >= len(self._pages) - 1:
            return
        self._goto_page(self._current_page + 1)

    def prev_page(self):
        if not self._pages or self._current_page <= 0:
            return
        self._goto_page(self._current_page - 1)

    def _goto_page(self, index):
        if not self._pages or not (0 <= index < len(self._pages)):
            return
        self._current_page = index
        self._finger_smooth = None
        self._finger_last_pt = None
        self._cursor_img_pos = None
        self._zoom = 1.0
        self._pan_x = 0
        self._pan_y = 0
        self._render()
        self.app.toolbar.update_zoom_label(self._zoom)
        self.app.sidebar.update_page_label(index + 1, len(self._pages))

    # ==================== cursor drawing ====================

    def _draw_cursor_only(self, ix, iy, color="#00e5ff"):
        sx = self._offset_x + int(ix * self._zoom)
        sy = self._offset_y + int(iy * self._zoom)
        r = 12
        self.canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            outline=color, width=3, fill="",
            tags="finger_cursor",
        )

    # ==================== page rendering ====================

    def display_images(self, pil_images):
        """Load a list of pages."""
        if not pil_images:
            return

        self._pages = [img.convert("RGB") for img in pil_images]
        self._overlays = []
        self._overlay_draws = []
        for page in self._pages:
            w, h = page.size
            ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            self._overlays.append(ov)
            self._overlay_draws.append(ImageDraw.Draw(ov))

        self._current_page = 0
        self._has_page = True
        self._zoom = 1.0
        self._pan_x = 0
        self._pan_y = 0
        self._finger_smooth = None
        self._finger_last_pt = None
        self._cursor_img_pos = None

        self._render()
        self.app.toolbar.update_zoom_label(self._zoom)
        self.app.sidebar.update_page_label(1, len(self._pages))

    def display_image(self, pil_image):
        """Single-page convenience."""
        self.display_images([pil_image])

    def display_blank_page(self, width=1200, height=850):
        blank = Image.new("RGB", (width, height), "white")
        self.display_images([blank])

    def clear_overlay(self):
        if not self._pages:
            return
        for i, page in enumerate(self._pages):
            w, h = page.size
            self._overlays[i] = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            self._overlay_draws[i] = ImageDraw.Draw(self._overlays[i])
        self._render()

    def _show_welcome(self):
        self._has_page = False
        self._pages = []
        self._overlays = []
        self._overlay_draws = []
        self.canvas.delete("all")
        self.canvas.create_text(
            600, 300,
            text="Upload a file or create a blank page",
            fill="#888888",
            font=("Segoe UI", 20),
        )

    def _render(self):
        if not self._pages:
            return

        page = self._pages[self._current_page]
        overlay = self._overlays[self._current_page]

        composed = page.copy()
        composed.paste(overlay, (0, 0), overlay)

        w0, h0 = composed.size
        disp_w = max(1, int(w0 * self._zoom))
        disp_h = max(1, int(h0 * self._zoom))

        if self._zoom != 1.0:
            composed = composed.resize((disp_w, disp_h), Image.LANCZOS)

        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width() or 1200
        ch = self.canvas.winfo_height() or 800

        self._offset_x = (cw - disp_w) // 2 + self._pan_x
        self._offset_y = (ch - disp_h) // 2 + self._pan_y

        self._photo = ImageTk.PhotoImage(composed)
        self.canvas.delete("all")
        self.canvas.create_image(
            self._offset_x, self._offset_y,
            image=self._photo, anchor="nw",
        )

        if self._cursor_img_pos is not None:
            self._draw_cursor_only(*self._cursor_img_pos)

    # ==================== mouse drawing ====================

    def _on_press(self, event):
        if not self._has_page:
            return
        x, y = self._to_image_coords(event)
        if not self._in_bounds(x, y):
            return
        self._drawing = True
        self._last_pt = (x, y)

    def _on_drag(self, event):
        if not self._drawing:
            return
        x, y = self._to_image_coords(event)
        w, h = self._pages[self._current_page].size
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        self._draw_segment(self._last_pt, (x, y))
        self._last_pt = (x, y)
        self._render()

    def _on_release(self, event):
        self._drawing = False
        self._last_pt = None

    def _draw_segment(self, p1, p2):
        color = self.app.current_color
        thickness = self.app.current_thickness
        r = max(thickness // 2, 1)
        draw = self._overlay_draws[self._current_page]
        draw.line([p1, p2], fill=color, width=thickness)
        for p in (p1, p2):
            draw.ellipse(
                [p[0] - r, p[1] - r, p[0] + r, p[1] + r],
                fill=color,
            )