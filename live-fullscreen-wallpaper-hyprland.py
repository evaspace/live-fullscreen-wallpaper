#!/usr/bin/env python3
"""Hyprland / Omarchy version: fullscreen YouTube in the browser plays as a live wallpaper via mpvpaper.
mpvpaper draws on the layer-shell background layer, above swaybg/hyprpaper: killing it brings your wallpaper back."""
import json
import os
import re
import time
import signal
import socket
import subprocess
import sys
import threading

BROWSERS = ("firefox", "chromium", "brave", "google-chrome", "zen")
PLAYERS = "firefox,chromium,brave"
FORMAT = "bv*[height<=720]"
state = {"title": None, "proc": None, "token": None}

def run(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return r.stdout.strip() if r.returncode == 0 else ""

def stop():
    if state["proc"]:
        state["proc"].terminate()
    state["title"] = state["proc"] = state["token"] = None

def play(title, token):
    # URL from MPRIS (exact video); falls back to a title search if the browser exposes none
    url = run("playerctl", "-p", PLAYERS, "metadata", "xesam:url")
    stream = run("yt-dlp", "-g", "-f", FORMAT, "--no-playlist",
                 url if "youtube.com/watch" in url else f"ytsearch1:{title}").split("\n")[0]
    if not stream or state["token"] != token:
        return
    pos = run("playerctl", "-p", PLAYERS, "position") or "0"  # read last: resolve lag is not added to drift
    state["proc"] = subprocess.Popen(
        ["mpvpaper", "-o", f"no-audio loop start={pos} input-ipc-server={SOCK}", "ALL", stream],
        stdout=subprocess.DEVNULL, stderr=open("/tmp/live-fullscreen-wallpaper-mpv.log", "w"))
    threading.Thread(target=resync, args=(state["proc"],), daemon=True).start()

SOCK = "/tmp/live-fullscreen-wallpaper-mpv.sock"

def mpv_cmd(*cmd):
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(1)
    s.connect(SOCK)
    s.sendall((json.dumps({"command": list(cmd)}) + "\n").encode())
    for line in s.makefile():  # skip async event lines until the command reply
        reply = json.loads(line)
        if "error" in reply:
            return reply.get("data")

def resync(proc):
    # shortcut: seeks on drift > 1.5 s, every 5 s; upgrade = playback-speed nudging for smoother catch-up
    time.sleep(3)
    while proc.poll() is None:
        try:
            pos = float(run("playerctl", "-p", PLAYERS, "position"))
            if abs(mpv_cmd("get_property", "time-pos") - pos) > 1.5:
                mpv_cmd("seek", pos, "absolute")
        except (OSError, ValueError, TypeError):
            pass
        time.sleep(5)

def youtube_title(client):
    if client["class"].lower() in BROWSERS and " - YouTube" in client["title"]:
        return re.sub(r"^\(\d+\)\s*", "", client["title"].split(" - YouTube")[0])

def update():
    clients = json.loads(run("hyprctl", "clients", "-j") or "[]")
    # "fullscreen" is a bool on old Hyprland, an int (0 = none) on recent ones
    title = next((youtube_title(c) for c in clients if c.get("fullscreen") and youtube_title(c)), None)
    if not title:
        stop()
    elif state["title"] != title or (state["proc"] and state["proc"].poll() is not None):
        stop()
        state["title"], state["token"] = title, object()
        threading.Thread(target=play, args=(title, state["token"]), daemon=True).start()

def main():
    signal.signal(signal.SIGTERM, lambda *_: (stop(), sys.exit(0)))
    path = f"{os.environ['XDG_RUNTIME_DIR']}/hypr/{os.environ['HYPRLAND_INSTANCE_SIGNATURE']}/.socket2.sock"
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(path)
    update()
    for line in sock.makefile():
        if line.split(">>")[0] in ("fullscreen", "activewindow", "closewindow", "workspace", "windowtitle"):
            update()

if __name__ == "__main__":
    main()
