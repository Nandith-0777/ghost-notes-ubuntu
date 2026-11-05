const { app, BrowserWindow } = require("electron");
app.whenReady().then(() => {
  let w = new BrowserWindow({
    x: 1280,
    y: 0,
    width: 1280,
    height: 720,
    frame: false,
    title: "Public capture fixture",
    backgroundColor: "#23a6d5",
  });
  w.loadURL(
    "data:text/html," +
      encodeURIComponent(
        `<html><style>body{margin:0;color:white;background:repeating-conic-gradient(#1c70a0 0% 25%,#ad4b51 0% 50%) 0 0/120px 120px;font:48px sans-serif;height:100vh}h1{margin:0;padding:100px 60px}</style><h1>PUBLIC BACKGROUND<br>Capture must show this behind the private note</h1></html>`,
      ),
  );
});
