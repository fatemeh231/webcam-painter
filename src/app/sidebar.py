import os
import customtkinter as ctk
from tkinter import filedialog
from files.file_loader import load_file_as_images


SUPPORTED_TYPES = [
    ("All supported",
     "*.pdf *.png *.jpg *.jpeg *.bmp *.gif *.webp *.md *.txt *.docx *.xlsx *.pptx"),
    ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
    ("PDF", "*.pdf"),
    ("Markdown / Text", "*.md *.txt"),
    ("Word", "*.docx"),
    ("Excel", "*.xlsx"),
    ("PowerPoint", "*.pptx"),
    ("All files", "*.*"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, width=250, corner_radius=0)
        self.app = app
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="Webcam Painter",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(24, 2), padx=16, anchor="w")

        ctk.CTkLabel(
            self,
            text="Annotate files with your finger",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 24), padx=16, anchor="w")

        ctk.CTkButton(
            self,
            text="Upload File",
            command=self._upload_file,
            height=42,
            corner_radius=8,
        ).pack(pady=6, padx=16, fill="x")

        ctk.CTkButton(
            self,
            text="Blank Page",
            command=self._new_blank,
            height=42,
            corner_radius=8,
            fg_color="#2d5a2d",
            hover_color="#3d7a3d",
        ).pack(pady=6, padx=16, fill="x")

        ctk.CTkLabel(
            self,
            text="Loaded file",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#aaaaaa",
        ).pack(pady=(28, 4), padx=16, anchor="w")

        self.file_label = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(size=11),
            text_color="#777777",
            wraplength=210,
            justify="left",
        )
        self.file_label.pack(padx=16, anchor="w")

        # ---------- Page navigation ----------
        ctk.CTkLabel(
            self,
            text="Page",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#aaaaaa",
        ).pack(pady=(24, 4), padx=16, anchor="w")

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(pady=4, padx=16, fill="x")

        self.page_prev_btn = ctk.CTkButton(
            nav,
            text="←",
            width=44,
            height=30,
            corner_radius=6,
            fg_color="#3a3a3a",
            hover_color="#505050",
            command=self._prev_page,
            state="disabled",
        )
        self.page_prev_btn.pack(side="left")

        self.page_label = ctk.CTkLabel(
            nav,
            text="—",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=60,
        )
        self.page_label.pack(side="left", expand=True)

        self.page_next_btn = ctk.CTkButton(
            nav,
            text="→",
            width=44,
            height=30,
            corner_radius=6,
            fg_color="#3a3a3a",
            hover_color="#505050",
            command=self._next_page,
            state="disabled",
        )
        self.page_next_btn.pack(side="right")

    # ---------------- actions ----------------

    def _upload_file(self):
        path = filedialog.askopenfilename(
            title="Choose a file",
            filetypes=SUPPORTED_TYPES,
        )
        if not path:
            return
        try:
            images = load_file_as_images(path)
            if not images:
                self.file_label.configure(text="Error: no pages found.")
                return
            self.app.canvas_view.display_images(images)
            self.app.loaded_file_path = path
            self.file_label.configure(text=os.path.basename(path))
        except Exception as e:
            self.file_label.configure(text=f"Error: {e}")

    def _new_blank(self):
        self.app.canvas_view.display_blank_page()
        self.app.loaded_file_path = None
        self.file_label.configure(text="(blank page)")

    def _prev_page(self):
        self.app.canvas_view.prev_page()

    def _next_page(self):
        self.app.canvas_view.next_page()

    def update_page_label(self, current, total):
        if total <= 1:
            self.page_label.configure(text="—")
            self.page_prev_btn.configure(state="disabled")
            self.page_next_btn.configure(state="disabled")
            return

        self.page_label.configure(text=f"{current} / {total}")
        self.page_prev_btn.configure(
            state="normal" if current > 1 else "disabled"
        )
        self.page_next_btn.configure(
            state="normal" if current < total else "disabled"
        )