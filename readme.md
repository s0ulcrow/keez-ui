# keez-ui

a minimal, customizable, and non-invasive virtual keyboard overlay for users with broken or malfunctioning keys.

## features

- **non-invasive:** uses windows api tweaks to trigger keys without stealing focus from your active window.
- **customizable layout:** add or modify the displayed keys on the fly using the settings tab.
- **always on top:** toggleable setting to keep the utility visible over other applications[cite: 1].
- **instant input:** typing delays are minimized for instant virtual key entry.

## installation & usage

you can run keezui using the standalone executable or directly from the python source code.

### option 1: standalone executable (.exe)
1. go to the **releases** section of this github repository.
2. download the latest compiled version.
3. run the executable.

### option 2: running from source

#### prerequisites
- python 3.x
- `pyautogui` library

```bash
pip install pyautogui
```

#### running the script
1. clone or download this repository.
2. ensure `app_icon.ico` is present in the root directory[cite: 1].
3. launch the application via the terminal:
```bash
python keez-main.py
```