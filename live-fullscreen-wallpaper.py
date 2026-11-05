#!/usr/bin/env python3
"""Fullscreen YouTube in Firefox becomes a live wallpaper behind transparent windows (i3 + picom).
The Firefox extension in extension/ streams the playing video to this script (no yt-dlp, no delay).
Other fullscreen windows (games...) get a black wallpaper. Otherwise your normal wallpaper."""
import i3ipc
from Xlib import X, Xatom, display
import subprocess
import os
import re
import time
import socket
import signal
import sys
import threading

# Configuration
HERE = os.path.dirname(os.path.realpath(__file__))
# Your normal wallpaper: LFW_WALLPAPER env var, else the first CLI argument
WALLPAPER = os.environ.get("LFW_WALLPAPER") or (sys.argv[1] if len(sys.argv) > 1 else None)
WALLPAPER_CMD = ["feh", "--bg-fill", WALLPAPER] if WALLPAPER else ["feh", "--bg-fill", os.path.join(HERE, "assets", "black.png")]
BLACK_CMD = ["feh", "--bg-fill", os.path.join(HERE, "assets", "black.png")]

BROWSERS = ("firefox",)  # the extension only exists for Firefox
# mpv uses the software x11 vo: its GPU/EGL/vaapi path was running when Xorg aborted in Mesa glamor
LIVE = os.environ.get("LFW_LIVE") != "0"  # LFW_LIVE=0 disables the live mode
SOCK = os.environ.get("LFW_SOCK") or f"{os.environ.get('XDG_RUNTIME_DIR', '/tmp')}/lfw.sock"
live = {"on": False, "proc": None}

def stop_live():
    live["on"] = False
    if live["proc"]:
        live["proc"].terminate()
        live["proc"] = None
    if "win" in live:
        live["win"].unmap()
        live["dpy"].sync()

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

def pump(conn):
    # One connection = one webm stream from the extension (header first), so mpv starts per connection.
    for _ in range(40):  # the DOM fullscreen event can beat the i3 one by a few ms
        if live["on"]:
            break
        time.sleep(0.05)
    else:
        conn.close()
        return
    if live["proc"]:
        live["proc"].terminate()
    proc = live["proc"] = subprocess.Popen(
        ["mpv", f"--wid={live['win'].id}", "--no-audio", "--vo=x11", "--hwdec=no", "--profile=low-latency",
         "--no-osc", "--no-input-default-bindings", "-"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=open("/tmp/live-fullscreen-wallpaper-mpv.log", "w"))
    try:
        while data := conn.recv(65536):
            proc.stdin.write(data)
            proc.stdin.flush()
    except OSError:  # mpv gone (BrokenPipe) or socket reset
        pass
    finally:
        conn.close()
        proc.terminate()

def serve():
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    srv = socket.socket(socket.AF_UNIX)
    srv.bind(SOCK)
    srv.listen(1)
    while True:
        threading.Thread(target=pump, args=(srv.accept()[0],), daemon=True).start()

def start_live():
    live["on"] = True
    desktop_window()  # black until the first frames arrive

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
        if not live["on"]:
            log(f"Live wallpaper: {yt}")
            start_live()
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
    threading.Thread(target=serve, daemon=True).start()
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
