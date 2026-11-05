#!/usr/bin/env python3
"""Firefox native messaging host: base64 webm chunks from the extension -> wallpaper daemon socket."""
import base64, json, os, socket, struct, sys

s = socket.socket(socket.AF_UNIX)
s.connect(os.environ.get("LFW_SOCK") or f"{os.environ.get('XDG_RUNTIME_DIR', '/tmp')}/lfw.sock")
inp = sys.stdin.buffer
while hdr := inp.read(4):
    (n,) = struct.unpack("=I", hdr)
    s.sendall(base64.b64decode(json.loads(inp.read(n))))
