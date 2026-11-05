#!/usr/bin/env python3
"""Load extension/ as a temporary add-on in a running Firefox started with `firefox --marionette`."""
import json, os, socket, sys, time

PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "extension")

def send(s, f, i, name, params):
    msg = json.dumps([0, i, name, params])
    s.sendall(f"{len(msg)}:{msg}".encode())
    n = b""
    while (c := f.read(1)) != b":":
        n += c
    return json.loads(f.read(int(n)))

for _ in range(60):  # Firefox needs a few seconds to open the port
    try:
        s = socket.create_connection(("127.0.0.1", 2828))
        break
    except OSError:
        time.sleep(0.5)
else:
    sys.exit("Marionette port 2828 closed: start Firefox with `firefox --marionette`")
f = s.makefile("rb")
n = b""
while (c := f.read(1)) != b":":  # server hello
    n += c
f.read(int(n))
send(s, f, 1, "WebDriver:NewSession", {"capabilities": {}})
print(send(s, f, 2, "Addon:Install", {"path": PATH, "temporary": True}))
