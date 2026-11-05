# live-fullscreen-wallpaper

Put a YouTube video fullscreen in Firefox/Chromium/Brave and it also plays as your **live wallpaper**, visible behind your transparent terminals on the other workspaces.

- YouTube fullscreen in Firefox: the extension streams the playing video to the desktop layer (muted, no delay, no yt-dlp).
- Any other fullscreen window (a game...): black wallpaper.
- No fullscreen: your normal wallpaper comes back.


![screenshot](docs/screenshot.png)

## Supported

| Session | Script | Notes |
|---|---|---|
| i3 + picom (X11) | `live-fullscreen-wallpaper.py` | any distro, `install.sh` handles pacman/apt/dnf/zypper |
| Hyprland (Omarchy, Arch...) | `live-fullscreen-wallpaper-hyprland.py` | needs `mpvpaper` |
| Sway, GNOME, KDE, other WMs | not supported | PRs welcome |

## Requirements

i3 on X11, a compositor ([picom](https://github.com/yshui/picom)) and transparent windows (e.g. alacritty `opacity = 0.85`), plus `mpv yt-dlp feh playerctl python-i3ipc python-xlib`. 

**Hyprland / Omarchy**: `live-fullscreen-wallpaper-hyprland.py` (Wayland, via `mpvpaper`), set up by `install.sh` when run inside a Hyprland session. Needs `mpv yt-dlp playerctl mpvpaper`, no picom. Untested on real Omarchy so far. Sway and GNOME/KDE are not supported.

## Install

```sh
git clone https://github.com/evaspace/live-fullscreen-wallpaper
cd live-fullscreen-wallpaper
./install.sh ~/Pictures/my-wallpaper.png   # pacman / apt / dnf / zypper
```

It adds one `exec_always` line to your i3 config. Reload i3 with `Mod+Shift+r`.
Let an AI agent do it for you: see [AI_INSTALL.md](AI_INSTALL.md), or copy `skill/` to `~/.claude/skills/live-fullscreen-wallpaper/` for Claude Code.

## How it works

1. i3ipc watches window events and finds a fullscreen Firefox window titled `... - YouTube`.
2. The extension (`extension/`) records the player with `captureStream()` + `MediaRecorder` (webm, 100 ms chunks) and sends it through native messaging (`lfw_host.py`) to a unix socket of the daemon.
3. The daemon pipes it to `mpv`, which plays it in a borderless `_NET_WM_WINDOW_TYPE_DESKTOP` window under everything. picom paints the root pixmap, not the root window, so a real window is needed.

## Limits

- Firefox only (Hyprland script still uses yt-dlp). DRM-protected (Widevine) videos cannot be captured: black wallpaper.
- Install the extension: sign it once (free, unlisted) with `web-ext sign -s extension --channel=unlisted --api-key=... --api-secret=...` (keys from addons.mozilla.org/developers/addon/api/key/), then open the `.xpi` in Firefox. Without signing, `firefox --marionette` + `./load_extension.py` loads it as a temporary add-on until the next restart.
- Cost while streaming: roughly one CPU core in total (Firefox decode + 1280 px VP8 encode + mpv software output).
- On an Intel Arc B580 + Mesa 26.2.6, mpv's default GPU output aborted Xorg twice (`abort()` in `libgallium` via `libglamoregl`). The script now forces `--vo=x11 --hwdec=no` (software, no GL/vaapi in the client), which avoids that path. If your X server still dies, set `LFW_LIVE=0`. The Hyprland version is not affected.
- Logs: `/tmp/live-fullscreen-wallpaper.log` and `/tmp/live-fullscreen-wallpaper-mpv.log`.

MIT license.
