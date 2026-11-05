#!/usr/bin/env bash
# Installs dependencies and hooks the script into i3, or Hyprland/Omarchy (Arch only for that one). Usage: ./install.sh [/path/to/wallpaper.png]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WALLPAPER="${1:-}"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

if command -v pacman >/dev/null; then
  $SUDO pacman -S --needed mpv yt-dlp feh playerctl python-i3ipc python-xlib
elif command -v apt-get >/dev/null; then
  $SUDO apt-get install -y mpv yt-dlp feh playerctl python3-i3ipc python3-xlib
elif command -v dnf >/dev/null; then
  $SUDO dnf install -y mpv yt-dlp feh playerctl python3-i3ipc python3-xlib
elif command -v zypper >/dev/null; then
  $SUDO zypper install -y mpv yt-dlp feh playerctl python3-i3ipc python3-python-xlib
else
  echo "Unknown package manager: install mpv yt-dlp feh playerctl + python i3ipc and python-xlib by hand." >&2
fi

for bin in i3 picom; do
  command -v "$bin" >/dev/null || echo "warning: '$bin' not found, it is required (see README)." >&2
done

if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
  # Hyprland / Omarchy: Wayland version, needs mpvpaper (extra or AUR)
  command -v mpvpaper >/dev/null || $SUDO pacman -S --needed mpvpaper 2>/dev/null || yay -S --needed mpvpaper
  chmod +x "$HERE/live-fullscreen-wallpaper-hyprland.py"
  HCFG="$HOME/.config/hypr/autostart.conf"; [ -f "$HCFG" ] || HCFG="$HOME/.config/hypr/hyprland.conf"
  grep -q live-fullscreen-wallpaper "$HCFG" || printf '\n# live-fullscreen-wallpaper\nexec-once = %s\n' "$HERE/live-fullscreen-wallpaper-hyprland.py" >> "$HCFG"
  echo "Added to $HCFG. Log out and in, or run the script once by hand."
  exit 0
fi

chmod +x "$HERE/live-fullscreen-wallpaper.py"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/i3/config"
LINE="exec_always --no-startup-id $HERE/live-fullscreen-wallpaper.py $WALLPAPER"
if [ -f "$CFG" ] && ! grep -q live-fullscreen-wallpaper "$CFG"; then
  printf '\n# live-fullscreen-wallpaper\n%s\n' "$LINE" >> "$CFG"
  echo "Added to $CFG. Reload i3 with Mod+Shift+r."
else
  echo "Add this line to your i3 config by hand: $LINE"
fi
