// While a YouTube player is fullscreen, stream it (downscaled to 1280 px, 30 fps, webm, 100 ms chunks) to the wallpaper.
let rec = null, port = null, queue = Promise.resolve();

const b64 = blob => new Promise(r => {
  const f = new FileReader();
  f.onload = () => r(f.result.slice(f.result.indexOf(",") + 1));
  f.readAsDataURL(blob);
});

function start() {
  const v = document.querySelector("video.html5-main-video") || document.querySelector("video");
  if (!v || !v.videoWidth || rec) return;
  try {
    port = browser.runtime.connect();
    // Encoding the native 1440p+ frames cost ~70 % of a core; a 1280 px canvas is plenty for a wallpaper.
    // shortcut: size fixed at start, a mid-fullscreen change of aspect ratio is stretched; upgrade = resize on loadedmetadata
    const c = document.createElement("canvas");
    c.width = 1280;
    c.height = Math.round(1280 * v.videoHeight / v.videoWidth);
    const g = c.getContext("2d", { alpha: false });
    const draw = () => { if (rec) { g.drawImage(v, 0, 0, c.width, c.height); v.requestVideoFrameCallback(draw); } };
    const stream = c.captureStream(30);
    rec = new MediaRecorder(stream, { mimeType: "video/webm;codecs=vp8", videoBitsPerSecond: 3e6 });
    // queue keeps chunks in order: FileReader completions are not guaranteed to be
    rec.ondataavailable = e => { queue = queue.then(async () => port.postMessage(await b64(e.data))); };
    rec.start(100);
    draw();
  } catch (err) { // e.g. DRM-protected video: captureStream/MediaRecorder refuse
    console.warn("lfw: capture failed", err);
    stop();
  }
}

function stop() {
  const p = port, r = rec;
  rec = port = null;
  if (r && r.state !== "inactive") r.stop();
  queue = queue.then(() => p && p.disconnect());
}

document.addEventListener("fullscreenchange", () => document.fullscreenElement ? start() : stop());
