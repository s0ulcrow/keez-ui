import tkinter as tk
from tkinter import ttk
import sys
import os

# this library handles direct typing simulation
try:
    import pyautogui
    pyautogui.PAUSE = 0.001  # removes the default delay for instant typing
except ImportError:
    pyautogui = None

class VirtualKeyboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KeezUI")
        self.geometry("400x100")
        
        # default configuration
        self.keys_list = ["2", "capslock", "s", "x"]
        self.always_on_top = True
        self.is_caps_on = False
        
        # load app icon from the same directory
        self.load_icon()
        
        self.apply_window_rules()
        self.build_ui()

    def load_icon(self):
        try:
            if getattr(sys, 'frozen', False):
                # pyinstaller extracts assets to a temporary folder named _MEIPASS
                script_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
            icon_path = os.path.join(script_dir, "app_icon.ico")
            
            # fallback: look next to the .exe if it wasn't bundled inside
            if not os.path.exists(icon_path) and getattr(sys, 'frozen', False):
                icon_path = os.path.join(os.path.dirname(sys.executable), "app_icon.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass
        
    def apply_window_rules(self):
        # set always on top state
        self.attributes("-topmost", self.always_on_top)
        
        # magic trick for windows: prevents this ui from stealing focus when clicked
        if sys.platform == "win32":
            self.update()  # force window generation to fetch id
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | WS_EX_NOACTIVATE)

    def build_ui(self):
        # create tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self.tab_keyboard = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_keyboard, text="keyboard")
        self.notebook.add(self.tab_settings, text="settings")

        self.render_keyboard_tab()
        self.render_settings_tab()

    def render_keyboard_tab(self):
        # clear old layout when updating keys
        for widget in self.tab_keyboard.winfo_children():
            widget.destroy()

        if not pyautogui:
            err_lbl = tk.Label(self.tab_keyboard, text="missing dependency!\nplease run: pip install pyautogui", fg="red", font=("Arial", 11))
            err_lbl.pack(expand=True)
            return

        btn_frame = ttk.Frame(self.tab_keyboard)
        btn_frame.pack(expand=True)

        for idx, key in enumerate(self.keys_list):
            clean_key = key.strip()
            label_text = clean_key
            
            # handle shift modifications for visual cues
            if clean_key.lower() in ["s", "x"]:
                label_text = clean_key.upper() if self.is_caps_on else clean_key.lower()
            elif clean_key.lower() == "capslock":
                label_text = "[caps]"

            btn = ttk.Button(btn_frame, text=label_text, width=8,
                             command=lambda k=clean_key: self.press_virtual_key(k))
            btn.grid(row=0, column=idx, padx=6, pady=12)

    def render_settings_tab(self):
        # list input configuration
        lbl = ttk.Label(self.tab_settings, text="enter keys to show (separate with commas):")
        lbl.pack(pady=(15, 2))
        
        self.entry_box = ttk.Entry(self.tab_settings, width=35)
        self.entry_box.insert(0, ", ".join(self.keys_list))
        self.entry_box.pack(pady=5)

        # always on top checkbutton
        self.top_flag = tk.BooleanVar(value=self.always_on_top)
        self.chk_box = ttk.Checkbutton(self.tab_settings, text="keep window on top automatically",
                                       variable=self.top_flag, command=self.update_topmost_behavior)
        self.chk_box.pack(pady=10)

        # save button
        save_btn = ttk.Button(self.tab_settings, text="apply changes", command=self.commit_settings)
        save_btn.pack(pady=5)

    def update_topmost_behavior(self):
        self.always_on_top = self.top_flag.get()
        self.attributes("-topmost", self.always_on_top)

    def commit_settings(self):
        user_input = self.entry_box.get()
        if user_input:
            self.keys_list = [item.strip() for item in user_input.split(",") if item.strip()]
        self.render_keyboard_tab()
        self.notebook.select(self.tab_keyboard)  # jump back to keyboard tab

    def press_virtual_key(self, key):
        if not pyautogui:
            return

        if key.lower() == "capslock":
            self.is_caps_on = not self.is_caps_on
            self.render_keyboard_tab()
            pyautogui.press("capslock")
            return

        # simulate live entry string
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