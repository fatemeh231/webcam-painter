import customtkinter as ctk


COLORS = [
    ("Black",  "#000000"),
    ("Red",    "#e53935"),
    ("Blue",   "#1e88e5"),
    ("White",  "#ffffff"),
    ("Pink",   "#ec407a"),
    ("Yellow", "#fdd835"),
    ("Orange", "#fb8c00"),
    ("Violet", "#8e24aa"),
]

THICKNESSES = [10, 30, 50, 70, 90, 100]


class Toolbar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=10)
        self.app = app
        self._camera_on = False
        self._build()

    def _build(self):
        # ---------- Pen colors ----------
        ctk.CTkLabel(
            self, text="Pen",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(12, 8), pady=12)

        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.pack(side="left", pady=12)

        self.color_buttons = {}
        for name, hex_code in COLORS:
            btn = ctk.CTkButton(
                color_frame,
                text="",
                width=22, height=22,
                fg_color=hex_code, hover_color=hex_code,
                border_width=2, border_color="#3a3a3a",
                corner_radius=11,
                command=lambda n=name, h=hex_code: self._select_color(n, h),
            )
            btn.pack(side="left", padx=2)
            self.color_buttons[name] = btn

        ctk.CTkFrame(self, width=2, fg_color="#3a3a3a").pack(
            side="left", fill="y", padx=8, pady=14)

        # ---------- Size ----------
        ctk.CTkLabel(
            self, text="Size",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8), pady=12)

        self.size_buttons = {}
        for size in THICKNESSES:
            btn = ctk.CTkButton(
                self, text=str(size),
                width=38, height=26,
                corner_radius=6,
                fg_color="#3a3a3a", hover_color="#505050",
                command=lambda s=size: self._select_thickness(s),
            )
            btn.pack(side="left", padx=2)
            self.size_buttons[size] = btn

        ctk.CTkFrame(self, width=2, fg_color="#3a3a3a").pack(
            side="left", fill="y", padx=8, pady=14)

        # ---------- Zoom ----------
        ctk.CTkLabel(
            self, text="Zoom",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8), pady=12)

        ctk.CTkButton(
            self, text="−", width=28, height=26,
            corner_radius=6,
            fg_color="#3a3a3a", hover_color="#505050",
            command=lambda: self.app.canvas_view.zoom_by(1/1.2),
        ).pack(side="left", padx=2)

        self.zoom_label = ctk.CTkButton(
            self, text="100%", width=52, height=26,
            corner_radius=6,
            fg_color="#3a3a3a", hover_color="#505050",
            command=lambda: self.app.canvas_view.reset_view(),
        )
        self.zoom_label.pack(side="left", padx=2)

        ctk.CTkButton(
            self, text="+", width=28, height=26,
            corner_radius=6,
            fg_color="#3a3a3a", hover_color="#505050",
            command=lambda: self.app.canvas_view.zoom_by(1.2),
        ).pack(side="left", padx=2)

        ctk.CTkFrame(self, width=2, fg_color="#3a3a3a").pack(
            side="left", fill="y", padx=8, pady=14)

        # ---------- Clear ----------
        ctk.CTkButton(
            self, text="Clear",
            width=56, height=26, corner_radius=6,
            fg_color="#8b1f1f", hover_color="#b02a2a",
            command=self._clear_all,
        ).pack(side="left", padx=(0, 6), pady=12)

        # ---------- Camera ----------
        self.camera_btn = ctk.CTkButton(
            self, text="Cam: OFF",
            width=96, height=26, corner_radius=6,
            fg_color="#2d5a2d", hover_color="#3d7a3d",
            command=self._toggle_camera,
        )
        self.camera_btn.pack(side="left", padx=(0, 10), pady=12)

        self._select_color("Black", "#000000")
        self._select_thickness(10)

    # ---------- state ----------

    def _select_color(self, name, hex_code):
        self.app.current_color = hex_code
        for n, btn in self.color_buttons.items():
            if n == name:
                btn.configure(border_color="#ffffff", border_width=3)
            else:
                btn.configure(border_color="#3a3a3a", border_width=2)

    def _select_thickness(self, size):
        self.app.current_thickness = size
        for s, btn in self.size_buttons.items():
            if s == size:
                btn.configure(fg_color="#1e88e5", hover_color="#1e88e5")
            else:
                btn.configure(fg_color="#3a3a3a", hover_color="#505050")

    def update_zoom_label(self, zoom):
        try:
            self.zoom_label.configure(text=f"{int(round(zoom * 100))}%")
        except Exception:
            pass

    def _clear_all(self):
        self.app.canvas_view.clear_overlay()

    def _toggle_camera(self):
        self.app.toggle_camera()
        self._camera_on = not self._camera_on
        if self._camera_on:
            self.camera_btn.configure(
                text="Cam: ON", fg_color="#1e88e5", hover_color="#1e88e5")
        else:
            self.camera_btn.configure(
                text="Cam: OFF", fg_color="#2d5a2d", hover_color="#3d7a3d")