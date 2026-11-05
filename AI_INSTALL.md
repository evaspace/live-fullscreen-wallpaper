# Prompt for an AI agent

Paste this to Claude Code, Codex, Gemini CLI or similar, from this repo's root:

> Install live-fullscreen-wallpaper on this machine. Check I use i3 on X11 with picom (`echo $XDG_SESSION_TYPE`, `pgrep -a picom`); stop and tell me if not. Run `./install.sh <path of my current wallpaper>` (ask me for the path; ask me to run any `sudo` command myself). Make sure my terminal is transparent. Reload i3 with `i3-msg reload`. Then ask me to play a YouTube video fullscreen and switch workspace; if it fails read `/tmp/live-fullscreen-wallpaper*.log` and fix the cause. Never use API keys or paid services.
