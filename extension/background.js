// Relay: one content-script port = one native host process = one stream to the wallpaper daemon.
browser.runtime.onConnect.addListener(p => {
  const n = browser.runtime.connectNative("lfw");
  p.onMessage.addListener(m => n.postMessage(m));
  p.onDisconnect.addListener(() => n.disconnect());
  n.onDisconnect.addListener(() => p.disconnect());
});
