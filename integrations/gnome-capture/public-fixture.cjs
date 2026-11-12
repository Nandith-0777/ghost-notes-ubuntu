const { app, BrowserWindow, powerSaveBlocker } = require("electron");
const path = require("node:path");
app.setPath(
  "userData",
  path.join(app.getPath("home"), "ghost-notes-gnome", "fixture-profile"),
);
app.whenReady().then(() => {
  powerSaveBlocker.start("prevent-display-sleep");
  const window = new BrowserWindow({
    x: 80,
    y: 60,
    width: 1120,
    height: 700,
    frame: false,
    alwaysOnTop: true,
    title: "Ghost Notes Public Capture Fixture",
    backgroundColor: "#17445c",
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  window.loadURL(
    "data:text/html," +
      encodeURIComponent(
        "<html><style>body{margin:0;background:repeating-conic-gradient(#17445c 0% 25%,#24718b 0% 50%) 0 0/80px 80px;color:white;font:30px sans-serif}h1{margin:60px}p{margin:60px}</style><h1>PUBLIC CAPTURE BACKGROUND</h1><p>Only this pattern should appear behind a private note.</p></html>",
      ),
  );
});
