#!/usr/bin/env python3
"""Fullscreen YouTube in your browser becomes a live wallpaper behind transparent windows (i3 + picom).
Other fullscreen windows (games...) get a black wallpaper. Otherwise your normal wallpaper."""
import i3ipc
from Xlib import X, Xatom, display
import subprocess
import os
import re
import signal
import sys
import threading

# Configuration
HERE = os.path.dirname(os.path.realpath(__file__))
# Your normal wallpaper: LFW_WALLPAPER env var, else the first CLI argument
WALLPAPER = os.environ.get("LFW_WALLPAPER") or (sys.argv[1] if len(sys.argv) > 1 else None)
WALLPAPER_CMD = ["feh", "--bg-fill", WALLPAPER] if WALLPAPER else ["feh", "--bg-fill", os.path.join(HERE, "assets", "black.png")]
BLACK_CMD = ["feh", "--bg-fill", os.path.join(HERE, "assets", "black.png")]

BROWSERS = ("firefox", "brave")
# Off by default: the live mode crashed Xorg (glamor/Mesa) once, see README. Enable with LFW_LIVE=1
LIVE = os.environ.get("LFW_LIVE") == "1"
live = {"title": None, "proc": None, "token": None}

def stop_live():
    if live["proc"]:
        live["proc"].terminate()
    if "win" in live:
        live["win"].unmap()
        live["dpy"].sync()
    live["title"] = live["proc"] = live["token"] = None

def desktop_window():
    # picom paints the root pixmap, not the root window: mpv needs its own window below everything
    if "win" not in live:
        d = display.Display()
        sc = d.screen()
        w = sc.root.create_window(0, 0, sc.width_in_pixels, sc.height_in_pixels, 0, sc.root_depth,
                                  override_redirect=True, background_pixel=0)
        w.change_property(d.intern_atom("_NET_WM_WINDOW_TYPE"), Xatom.ATOM,
                          32, [d.intern_atom("_NET_WM_WINDOW_TYPE_DESKTOP")])
        live["win"], live["dpy"] = w, d
    live["win"].map()
    live["win"].configure(stack_mode=X.Below)
    live["dpy"].sync()
    return live["win"]

PLAYERS = "firefox,chromium,brave"
FORMAT = "bv*[height<=720]"

def playerctl(*args):
    r = subprocess.run(["playerctl", "-p", PLAYERS, *args], capture_output=True, text=True, check=False)
    return r.stdout.strip() if r.returncode == 0 else ""

def resolve(target):
    r = subprocess.run(["yt-dlp", "-g", "-f", FORMAT, "--no-playlist", target],
                       capture_output=True, text=True, check=False)
    return r.stdout.split("\n")[0] if r.returncode == 0 else None

def play(title, token):
    # URL from MPRIS (exact video); falls back to a title search if the browser exposes none
    url = playerctl("metadata", "xesam:url")
    stream = resolve(url if "youtube.com/watch" in url else f"ytsearch1:{title}")
    if not stream or live["token"] != token:
        return
    # read the position last, so the startup lag of the resolve step is not added to the drift
    pos = playerctl("position") or "0"
    live["proc"] = subprocess.Popen(
        ["mpv", f"--wid={live['win'].id}", "--no-audio", "--loop", "--no-osc",
         "--no-input-default-bindings", f"--start={pos}", stream],
        stdout=subprocess.DEVNULL, stderr=open("/tmp/live-fullscreen-wallpaper-mpv.log", "w"))

def start_live(title):
    if live["title"] == title and (live["proc"] is None or live["proc"].poll() is None):
        return
    stop_live()
    desktop_window()
    live["title"] = title
    live["token"] = object()
    threading.Thread(target=play, args=(title, live["token"]), daemon=True).start()

def youtube_title(leaf):
    if leaf.window_class and leaf.window_class.lower() in BROWSERS and " - YouTube" in (leaf.name or ""):
        return re.sub(r"^\(\d+\)\s*", "", leaf.name.split(" - YouTube")[0])

def log(msg):
    with open("/tmp/live-fullscreen-wallpaper.log", "a") as f:
        f.write(msg + "\n")

def update_wallpaper(i3, e=None):
    tree = i3.get_tree()
    fullscreen = False
    yt = None
    
    # Check all windows in the tree for fullscreen mode
    for leaf in tree.leaves():
        if leaf.fullscreen_mode != 0:
            fullscreen = True
            yt = youtube_title(leaf)
            log(f"Fullscreen detected on window: {leaf.name}")
            break
            
    if yt and LIVE:
        log(f"Live wallpaper: {yt}")
        start_live(yt)
    elif fullscreen:
        stop_live()
        log("Setting background to BLACK")
        subprocess.run(BLACK_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        stop_live()
        log("Restoring WALLPAPER")
        subprocess.run(WALLPAPER_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    log("--- Script Started ---")
    signal.signal(signal.SIGTERM, lambda *_: (stop_live(), sys.exit(0)))
    i3 = i3ipc.Connection()
    
    # Initial check
    update_wallpaper(i3)
    
    # Listen for any window state change or focus change
    i3.on("window::fullscreen_mode", update_wallpaper)
    i3.on("window::focus", update_wallpaper)
    i3.on("window::close", update_wallpaper)
    i3.on("workspace::focus", update_wallpaper)
    
    i3.main()

if __name__ == "__main__":
    main()
