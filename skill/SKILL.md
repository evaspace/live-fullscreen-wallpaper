---
name: live-fullscreen-wallpaper
description: Install or debug live-fullscreen-wallpaper, which turns a fullscreen YouTube video into the live wallpaper behind transparent windows on i3 + picom. Use when the user wants a video wallpaper on fullscreen, or when that script misbehaves.
---

1. Check `echo $XDG_SESSION_TYPE` is `x11`, `i3` and `picom` run. Otherwise stop: unsupported.
2. Run `./install.sh <wallpaper path>` from the repo (ask the user to run the `sudo` parts).
3. `i3-msg reload`, then ask the user to play a YouTube video fullscreen and switch workspace.
4. If nothing shows: read `/tmp/live-fullscreen-wallpaper.log` and `/tmp/live-fullscreen-wallpaper-mpv.log`. Common causes: missing `playerctl`/`yt-dlp`, outdated `yt-dlp`, picom not running.
