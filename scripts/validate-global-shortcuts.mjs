import assert from "node:assert/strict";
import { evaluate } from "/home/nandith/Work/ghost-notes-linux/scripts/cdp.mjs";
import { execFileSync } from "node:child_process";
assert.ok(
  process.env.GHOST_NOTES_TEST_KEYBOARD,
  "Set GHOST_NOTES_TEST_KEYBOARD to the compiled virtual-keyboard fixture",
);
assert.ok(
  (await evaluate(9346, "", "process.env.GHOST_NOTES_DATA_DIR"))?.startsWith(
    "/tmp/",
  ),
  "Use a disposable test profile",
);
const shortcuts = await evaluate(
  9346,
  "",
  `process.mainModule.require('./manager/shortcuts').getShortcuts()`,
);
for (const [id, key] of [
  ["newNoteAnywhere", "J"],
  ["openManagerAnywhere", "K"],
  ["toggleHideAllAnywhere", "L"],
  ["toggleGhostAllAnywhere", "U"],
])
  assert.equal(
    shortcuts.find((s) => s.id === id)?.accelerator,
    "Ctrl+Alt+Shift+" + key,
    "Configure test-only key combinations before running",
  );
const pause = () => new Promise((r) => setTimeout(r, 1200));
const hy = (...args) =>
  JSON.parse(execFileSync("hyprctl", args, { encoding: "utf8" }));
const ghostPid = await evaluate(9346, "", "process.pid");
const background = hy("-j", "clients").find(
  (c) => c.initialTitle === "Public capture fixture",
);
assert.ok(background);
async function backgroundFocus() {
  execFileSync("hyprctl", [
    "dispatch",
    `hl.dsp.focus({window="address:${background.address}"})`,
  ]);
  await pause();
  assert.equal(hy("-j", "activewindow").pid, background.pid);
  assert.notEqual(background.pid, ghostPid);
}
async function key(key) {
  await backgroundFocus();
  execFileSync(process.env.GHOST_NOTES_TEST_KEYBOARD, [
    String({ j: 36, k: 37, l: 38, u: 22 }[key]),
  ]);
  await pause();
}
const noteCount = () =>
  evaluate(
    9346,
    "",
    `process.mainModule.require('electron').BrowserWindow.getAllWindows().filter(w=>w.webContents.getURL().includes('note.html')).length`,
  );
const results = [];
const count = await noteCount();
await key("j");
assert.equal(await noteCount(), count + 1);
results.push("New note works with another app focused");
await key("k");
assert.ok(
  (await (await fetch("http://127.0.0.1:9345/json")).json()).some((p) =>
    p.url.includes("manager.html"),
  ),
);
results.push("Manager opens with another app focused");
const snapshot = () =>
  evaluate(
    9345,
    "manager.html",
    `window.manager.list().then(s=>s.notes.map(n=>({id:n.id,visible:n.visible,ghost:n.ghost})))`,
  );
await key("l");
assert.ok((await snapshot()).every((n) => !n.visible));
results.push("Hide all works from another app");
await key("l");
assert.ok((await snapshot()).every((n) => n.visible));
results.push("Show all works from another app");
await key("u");
assert.ok((await snapshot()).every((n) => n.ghost));
results.push("Click-through enables from another app");
await key("u");
assert.ok((await snapshot()).every((n) => !n.ghost));
results.push("Click-through disables from another app");
await key("l");
assert.ok((await snapshot()).every((n) => !n.visible));
await key("k");
results.push("Manager remains reachable with all notes hidden");
console.log(JSON.stringify({ passed: results.length, results }, null, 2));
