import tkinter as tk
from tkinter import ttk
import sys
import os
import math

try:
    import pyautogui
    pyautogui.PAUSE = 0.001
except ImportError:
    pyautogui = None


class RoundedButton(tk.Canvas):
    """A flat, rounded, themed button drawn on a Canvas (no more square 90s tk.Button look)."""

    def __init__(self, parent, text, command=None, width=72, height=58,
                 radius=14, bg="#1e1e1e", fg="#ffffff", hover_bg=None,
                 parent_bg="#121212", font=("Segoe UI", 13, "bold")):
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                          highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self.bg_color = bg
        self.hover_color = hover_bg or bg
        self.fg_color = fg
        self.font = font
        self.text = text
        self.radius = radius
        self.w = width
        self.h = height

        self._draw(self.bg_color)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self._draw(self.hover_color))
        self.bind("<Leave>", lambda e: self._draw(self.bg_color))

    def _draw(self, fill):
        self.delete("all")
        r = self.radius
        w, h = self.w, self.h
        pts = [
            r, 0, w - r, 0, w, 0, w, r,
            w, h - r, w, h, w - r, h, r, h,
            0, h, 0, h - r, 0, r, 0, 0,
        ]
        self.create_polygon(pts, smooth=True, fill=fill, outline="")
        self.create_text(w / 2, h / 2, text=self.text, fill=self.fg_color, font=self.font)

    def _on_click(self, event):
        if self.command:
            self.command()

    def set_active(self, is_active, active_fill):
        """Force a highlighted 'on' look (used for capslock toggle state)."""
        self.bg_color = active_fill if is_active else self.bg_color
        self._draw(self.bg_color)


class VirtualKeyboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KeezUI")

        # seamless window configurations
        self.overrideredirect(True)
        self.attributes("-alpha", 0.92)
        self.always_on_top = True

        # state management
        self.keys_list = ["2", "capslock", "s", "x"]
        self.is_caps_on = False
        self.orientation = "horizontal"
        self.active_theme = "dark"
        self.snap_position = "bottom right"
        self.in_settings_view = False

        self.themes = {
            "dark":   {"bg": "#121212", "key": "#1e1e1e", "fg": "#f2f2f2",
                       "active": "#2a2a2a", "accent": "#5E5E5E", "border": "#232323"},
            "light":  {"bg": "#f4f4f6", "key": "#ffffff", "fg": "#1a1a1a",
                       "active": "#e7e9ee", "accent": "#1e1e1e", "border": "#e2e2e2"},
            "grunge": {"bg": "#242221", "key": "#363230", "fg": "#e4dcd1",
                       "active": "#443e3a", "accent": "#c98a4b", "border": "#3a3532"},
        }

        # baseline layout dimensions
        self.item_size = 64  # keys are square now, not rectangular
        self.gap = 8
        self.pad = 32
        self.base_h = 98

        # fetch exact monitor boundaries
        self.sw = self.winfo_screenwidth()
        self.sh = self.winfo_screenheight()

        # the "work area" is the usable screen region that excludes the
        # taskbar. Snapping against this (instead of the raw screen size)
        # is what keeps the window from ever overlapping the taskbar.
        self.work_left, self.work_top, self.work_right, self.work_bottom = self.get_work_area()
        self.work_w = self.work_right - self.work_left
        self.work_h = self.work_bottom - self.work_top

        # tracking variables for current true position
        self.win_x = 0
        self.win_y = 0

        # cache of the last actually-rendered content size (measured, not
        # guessed) — used so position changes don't have to re-derive size
        self.current_w = 0
        self.current_h = 0

        # animation loop reference tracking
        self.tween_job = None

        # grid layout tracking (recomputed on every render so buttons never
        # get pushed off-screen no matter how many keys are configured)
        self.grid_cols = 1
        self.grid_rows = 1

        self.load_icon()
        self.apply_window_rules()

        self.main_container = tk.Frame(self)
        self.main_container.pack(expand=True, fill="both")

        self.show_keyboard_view()

        # periodically re-assert topmost/lift so alt-tabbing or switching
        # windows never leaves KeezUI stuck behind something else
        self.after(1500, self.reassert_topmost)

    def get_work_area(self):
        if sys.platform == "win32":
            try:
                import ctypes

                class RECT(ctypes.Structure):
                    _fields_ = [
                        ("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long),
                    ]

                SPI_GETWORKAREA = 0x0030
                rect = RECT()
                ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                if rect.right > rect.left and rect.bottom > rect.top:
                    return rect.left, rect.top, rect.right, rect.bottom
            except Exception:
                pass
        return 0, 0, self.sw, self.sh

    def reassert_topmost(self):
        try:
            self.attributes("-topmost", True)
            self.lift()
        except Exception:
            pass
        self.after(1500, self.reassert_topmost)

    def load_icon(self):
        try:
            if getattr(sys, 'frozen', False):
                script_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

    def apply_window_rules(self):
        self.attributes("-topmost", True)
        if sys.platform == "win32":
            self.update()
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | WS_EX_NOACTIVATE)

    def compute_grid(self, total_items):
        if self.orientation == "horizontal":
            available_w = self.work_w - (self.pad * 2)
            max_per_line = max(3, available_w // (self.item_size + self.gap))
            cols = min(total_items, max_per_line)
            rows = math.ceil(total_items / cols)
        else:
            available_h = self.work_h - (self.pad * 2) - 40
            max_per_line = max(3, available_h // (self.item_size + self.gap))
            rows = min(total_items, max_per_line)
            cols = math.ceil(total_items / rows)

        self.grid_cols = cols
        self.grid_rows = rows
        return cols, rows

    def calculate_snap_coordinates(self, w, h):
        edge_margin = 14

        if self.snap_position == "bottom left":
            x = self.work_left + edge_margin
            y = self.work_bottom - h - edge_margin
        elif self.snap_position == "bottom middle":
            x = self.work_left + (self.work_w // 2) - (w // 2)
            y = self.work_bottom - h - edge_margin
        else:  # bottom right
            x = self.work_right - w - edge_margin
            y = self.work_bottom - h - edge_margin

        if x < self.work_left: x = self.work_left
        if y < self.work_top: y = self.work_top
        if x + w > self.work_right: x = self.work_right - w
        if y + h > self.work_bottom: y = self.work_bottom - h

        return x, y

    def update_geometry_instantly(self, w, h):
        if self.tween_job:
            self.after_cancel(self.tween_job)
            self.tween_job = None
        self.win_x, self.win_y = self.calculate_snap_coordinates(w, h)
        self.geometry(f"{w}x{h}+{self.win_x}+{self.win_y}")

    def animate_to_position(self, w, h, steps=15, current_step=0, start_x=None, start_y=None, target_x=None, target_y=None):
        if current_step == 0:
            if self.tween_job:
                self.after_cancel(self.tween_job)
            start_x, start_y = self.win_x, self.win_y
            target_x, target_y = self.calculate_snap_coordinates(w, h)

            if start_x == target_x and start_y == target_y:
                self.geometry(f"{w}x{h}+{target_x}+{target_y}")
                return

        if current_step <= steps:
            t = current_step / steps
            ratio = (1 - math.cos(t * math.pi)) / 2

            self.win_x = int(start_x + (target_x - start_x) * ratio)
            self.win_y = int(start_y + (target_y - start_y) * ratio)

            self.geometry(f"{w}x{h}+{self.win_x}+{self.win_y}")

            self.tween_job = self.after(10, lambda: self.animate_to_position(
                w, h, steps, current_step + 1, start_x, start_y, target_x, target_y
            ))
        else:
            self.win_x, self.win_y = target_x, target_y
            self.geometry(f"{w}x{h}+{self.win_x}+{self.win_y}")
            self.tween_job = None

    def get_view_dimensions(self):
        if self.in_settings_view:
            return self.current_w, self.current_h

        if self.current_w and self.current_h:
            return self.current_w, self.current_h

        total_items = len(self.keys_list) + 2
        cols, rows = self.compute_grid(total_items)
        w = cols * (self.item_size + self.gap) + self.pad
        h = rows * (self.item_size + self.gap) + self.pad
        return w, h

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def _grid_position(self, idx):
        if self.orientation == "horizontal":
            row = idx // self.grid_cols
            col = idx % self.grid_cols
        else:
            col = idx // self.grid_rows
            row = idx % self.grid_rows
        return row, col

    def show_keyboard_view(self):
        self.in_settings_view = False
        self.clear_container()
        t = self.themes[self.active_theme]
        self.main_container.config(bg=t["bg"])
        self.config(bg=t["bg"])

        total_items = len(self.keys_list) + 2
        self.compute_grid(total_items)

        if not pyautogui:
            err = tk.Label(self.main_container, text="missing pyautogui", fg="#ff6b6b",
                            bg=t["bg"], font=("Segoe UI", 9))
            err.grid(row=0, column=0, columnspan=max(self.grid_cols, 1), padx=20, pady=20)
            self.main_container.update_idletasks()
            self.current_w = self.main_container.winfo_reqwidth()
            self.current_h = self.main_container.winfo_reqheight()
            self.update_geometry_instantly(self.current_w, self.current_h)
            return

        for idx, key in enumerate(self.keys_list):
            clean_key = key.strip()
            label_text = clean_key

            if clean_key.lower() in ["s", "x"]:
                label_text = clean_key.upper() if self.is_caps_on else clean_key.lower()
            elif clean_key.lower() == "capslock":
                label_text = "caps"

            is_caps_key = clean_key.lower() == "capslock"
            fill = t["accent"] if (is_caps_key and self.is_caps_on) else t["key"]
            fg = "#ffffff" if (is_caps_key and self.is_caps_on) else t["fg"]

            btn = RoundedButton(
                self.main_container, text=label_text,
                command=lambda k=clean_key: self.press_virtual_key(k),
                width=self.item_size,
                height=self.item_size, radius=14,
                bg=fill, fg=fg, hover_bg=t["active"], parent_bg=t["bg"],
            )
            row, col = self._grid_position(idx)
            btn.grid(row=row, column=col, padx=self.gap // 2, pady=self.gap // 2)

        cfg_idx = len(self.keys_list)
        cfg_btn = RoundedButton(
            self.main_container, text="⚙", command=self.show_settings_view,
            width=self.item_size,
            height=self.item_size, radius=14,
            bg=t["key"], fg=t["fg"], hover_bg=t["active"], parent_bg=t["bg"],
            font=("Segoe UI", 12),
        )
        row, col = self._grid_position(cfg_idx)
        cfg_btn.grid(row=row, column=col, padx=self.gap // 2, pady=self.gap // 2)

        exit_idx = cfg_idx + 1
        exit_btn = RoundedButton(
            self.main_container, text="✕", command=self.quit,
            width=self.item_size,
            height=self.item_size, radius=14,
            bg=t["key"], fg=t["fg"], hover_bg=t["active"], parent_bg=t["bg"],
            font=("Segoe UI", 12, "bold"),
        )
        row, col = self._grid_position(exit_idx)
        exit_btn.grid(row=row, column=col, padx=self.gap // 2, pady=self.gap // 2)

        self.main_container.update_idletasks()
        self.current_w = self.main_container.winfo_reqwidth()
        self.current_h = self.main_container.winfo_reqheight()
        self.update_geometry_instantly(self.current_w, self.current_h)

    def show_settings_view(self):
        self.in_settings_view = True
        self.clear_container()
        t = self.themes[self.active_theme]
        self.main_container.config(bg=t["bg"])
        self.config(bg=t["bg"])

        # 1. return arrow navigation button
        back_btn = RoundedButton(
            self.main_container, text="←", command=self.show_keyboard_view,
            width=56, height=self.item_size, radius=14,
            bg=t["key"], fg=t["fg"], hover_bg=t["active"], parent_bg=t["bg"],
            font=("Segoe UI", 14, "bold"),
        )
        back_btn.grid(row=0, column=0, padx=(16, 8), pady=14)

        label_font = ("Segoe UI", 9, "bold")

        # 2. key customization panel segment
        entry_frame = tk.Frame(self.main_container, bg=t["bg"])
        entry_frame.grid(row=0, column=1, padx=10, pady=5)
        lbl = tk.Label(entry_frame, text="KEYS", fg=t["accent"], bg=t["bg"], font=label_font)
        lbl.pack(anchor="w", pady=(0, 4))

        self.entry_box = tk.Entry(
            entry_frame, bg=t["key"], fg=t["fg"], insertbackground=t["fg"],
            bd=0, relief="flat", font=("Segoe UI", 10), width=18,
            highlightthickness=1, highlightbackground=t["border"], highlightcolor=t["accent"],
        )
        self.entry_box.insert(0, ", ".join(self.keys_list))
        self.entry_box.pack(fill="x", ipady=5)
        self.entry_box.bind("<KeyRelease>", lambda e: self.live_update_keys())

        # 3. layout orientation
        orient_frame = tk.Frame(self.main_container, bg=t["bg"])
        orient_frame.grid(row=0, column=2, padx=10, pady=5)
        tk.Label(orient_frame, text="LAYOUT", fg=t["accent"], bg=t["bg"], font=label_font).pack(anchor="w", pady=(0, 4))

        orient_row = tk.Frame(orient_frame, bg=t["bg"])
        orient_row.pack(anchor="w")
        for value, label in (("horizontal", "horiz"), ("vertical", "vert")):
            selected = self.orientation == value
            RoundedButton(
                orient_row, text=label, command=lambda v=value: self.set_orientation(v),
                width=52, height=32, radius=10,
                bg=t["accent"] if selected else t["key"],
                fg="#ffffff" if selected else t["fg"],
                hover_bg=t["active"], parent_bg=t["bg"],
                font=("Segoe UI", 9, "bold"),
            ).pack(side="left", padx=(0, 6), pady=2)

        # 4. positional snapping settings
        snap_frame = tk.Frame(self.main_container, bg=t["bg"])
        snap_frame.grid(row=0, column=3, padx=10, pady=5)
        tk.Label(snap_frame, text="SNAP POSITION", fg=t["accent"], bg=t["bg"], font=label_font).pack(anchor="w", pady=(0, 4))

        positions = ["bottom left", "bottom middle", "bottom right"]
        self.snap_var = tk.StringVar(value=self.snap_position)

        snap_menu = tk.OptionMenu(snap_frame, self.snap_var, *positions, command=lambda _: self.live_apply_position_tween())
        snap_menu.config(bg=t["key"], fg=t["fg"], activebackground=t["active"], activeforeground=t["fg"],
                          relief="flat", bd=0, highlightthickness=0, font=("Segoe UI", 9))
        snap_menu["menu"].config(bg=t["key"], fg=t["fg"], activebackground=t["active"], activeforeground=t["fg"])
        snap_menu.pack(fill="x", ipady=3)

        # 5. theme
        theme_frame = tk.Frame(self.main_container, bg=t["bg"])
        theme_frame.grid(row=0, column=4, padx=(10, 16), pady=5)
        tk.Label(theme_frame, text="THEME", fg=t["accent"], bg=t["bg"], font=label_font).pack(anchor="w", pady=(0, 4))

        self.theme_var = tk.StringVar(value=self.active_theme)
        theme_names = list(self.themes.keys())
        theme_menu = tk.OptionMenu(theme_frame, self.theme_var, *theme_names, command=lambda v: self.set_theme(v))
        theme_menu.config(bg=t["key"], fg=t["fg"], activebackground=t["active"], activeforeground=t["fg"],
                           relief="flat", bd=0, highlightthickness=0, font=("Segoe UI", 9))
        theme_menu["menu"].config(bg=t["key"], fg=t["fg"], activebackground=t["active"], activeforeground=t["fg"])
        theme_menu.pack(fill="x", ipady=3)

        # dynamically calculate size to prevent the window from blowing up to 980px wide
        self.main_container.update_idletasks()
        self.current_w = self.main_container.winfo_reqwidth()
        self.current_h = self.main_container.winfo_reqheight()
        self.update_geometry_instantly(self.current_w, self.current_h)

    def live_update_keys(self):
        user_input = self.entry_box.get()
        self.keys_list = [item.strip() for item in user_input.split(",") if item.strip()]

    def set_orientation(self, value):
        self.orientation = value
        self.show_settings_view()

    def set_theme(self, value):
        self.active_theme = value
        self.show_settings_view()

    def live_apply_position_tween(self):
        self.snap_position = self.snap_var.get()
        w, h = self.get_view_dimensions()
        self.animate_to_position(w, h)

    def press_virtual_key(self, key):
        if not pyautogui:
            return

        if key.lower() == "capslock":
            self.is_caps_on = not self.is_caps_on
            self.show_keyboard_view()
            pyautogui.press("capslock")
            return

        if key.lower() in ["s", "x"]:
            output_char = key.upper() if self.is_caps_on else key.lower()
            pyautogui.write(output_char)
        else:
            if len(key) > 1:
                pyautogui.press(key.lower())
            else:
                pyautogui.write(key)


if __name__ == "__main__":
    app = VirtualKeyboardApp()
    app.mainloop()