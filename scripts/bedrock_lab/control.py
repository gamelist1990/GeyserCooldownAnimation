#!/usr/bin/env python3
"""X11 control/capture for the explicitly authorized Bedrock test window only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

try:
    from Xlib import X, XK, display
    from Xlib.ext import xtest
except ImportError:
    sys.path.insert(0, "/usr/lib/bedrock-on-linux")
    from Xlib import X, XK, display
    from Xlib.ext import xtest


class GameWindow:
    def __init__(self):
        self.display = display.Display()
        matches = []
        for w in self.display.screen().root.query_tree().children:
            try:
                if w.get_wm_name() == "Minecraft" and w.get_geometry().width > 300:
                    matches.append(w)
            except Exception:
                pass
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one Minecraft window; found {len(matches)}")
        self.window = matches[0]
        self.held = set()

    def focus(self):
        self.window.configure(stack_mode=X.Above)
        self.window.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.display.sync()

    def key(self, key, down=True):
        symbol = XK.string_to_keysym(key)
        if not symbol:
            raise ValueError(f"Unknown X keysym: {key}")
        code = self.display.keysym_to_keycode(symbol)
        xtest.fake_input(self.display, X.KeyPress if down else X.KeyRelease, code)
        if down:
            self.held.add(key)
        else:
            self.held.discard(key)
        self.display.sync()

    def tap(self, key):
        self.key(key)
        time.sleep(0.06)
        self.key(key, False)

    def text(self, text):
        for char in text:
            symbol = ord(char) if char != "\n" else XK.string_to_keysym("Return")
            code = self.display.keysym_to_keycode(symbol)
            if not code:
                raise ValueError(f"Character unavailable in keyboard map: {char!r}")
            shifted = self.display.keycode_to_keysym(code, 0) != symbol
            if shifted:
                self.key("Shift_L")
            xtest.fake_input(self.display, X.KeyPress, code)
            self.display.sync()
            time.sleep(0.06)
            xtest.fake_input(self.display, X.KeyRelease, code)
            if shifted:
                self.key("Shift_L", False)
            self.display.sync()
            time.sleep(0.06)

    def scroll(self, x, y, steps):
        self.focus()
        self.window.warp_pointer(x, y)
        self.display.sync()
        time.sleep(0.2)
        for _ in range(abs(steps)):
            button = 5 if steps > 0 else 4
            xtest.fake_input(self.display, X.ButtonPress, button)
            self.display.sync()
            time.sleep(0.08)
            xtest.fake_input(self.display, X.ButtonRelease, button)
            self.display.sync()
            time.sleep(0.12)

    def click(self, x, y):
        self.focus()
        self.window.warp_pointer(x, y)
        self.display.sync()
        time.sleep(0.1)
        xtest.fake_input(self.display, X.ButtonPress, 1)
        self.display.sync()
        time.sleep(0.15)
        xtest.fake_input(self.display, X.ButtonRelease, 1)
        self.display.sync()

    def capture(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
            "-window_id", str(self.window.id), "-framerate", "1", "-i", os.environ["DISPLAY"],
            "-frames:v", "1", "-y", str(path)], check=True, timeout=15)

    def release(self):
        for key in list(self.held):
            self.key(key, False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["probe", "capture", "click", "scroll", "key", "text", "resize"])
    p.add_argument("values", nargs="*")
    args = p.parse_args()
    game = GameWindow()
    try:
        if args.action == "probe":
            g = game.window.get_geometry()
            print(json.dumps({"window_id": game.window.id, "width": g.width, "height": g.height,
                              "display": os.environ["DISPLAY"]}))
        elif args.action == "capture":
            game.capture(args.values[0])
        elif args.action == "resize":
            if len(args.values) != 2:
                raise ValueError("resize requires width and height")
            width, height = map(int, args.values)
            if not (960 <= width <= 1920 and 700 <= height <= 1080):
                raise ValueError("Unsupported lab window dimensions")
            game.window.configure(x=0, y=0, width=width, height=height)
            game.display.sync()
            print(json.dumps({"width": game.window.get_geometry().width,
                              "height": game.window.get_geometry().height}))
        elif args.action == "click":
            game.click(*map(int, args.values))
        elif args.action == "scroll":
            game.scroll(*map(int, args.values))
        elif args.action == "key":
            game.focus()
            for key in args.values:
                game.tap(key)
        elif args.action == "text":
            game.focus()
            game.text(" ".join(args.values))
    finally:
        game.release()


if __name__ == "__main__":
    main()
