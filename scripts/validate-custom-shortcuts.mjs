import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { evaluate } from "./cdp.mjs";
const keyboard = process.env.GHOST_NOTES_TEST_KEYBOARD;
assert.ok(
  keyboard,
  "Set GHOST_NOTES_TEST_KEYBOARD to the compiled keyboard fixture",
);
assert.ok(
  (await evaluate(9346, "", "process.env.GHOST_NOTES_DATA_DIR"))?.startsWith(
    "/tmp/",
  ),
  "Use a disposable profile",
);
const ui = (expression) => evaluate(9345, "manager.html", expression);
const pause = () => new Promise((resolve) => setTimeout(resolve, 250));
const count = () =>
  evaluate(
    9346,
    "",
    `process.mainModule.require('electron').BrowserWindow.getAllWindows().filter(w=>w.webContents.getURL().includes('note.html')).length`,
  );
async function focus() {
  await evaluate(
    9346,
    "",
    `(()=>{const w=process.mainModule.require('electron').BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().includes('manager.html'));w.show();w.focus();return true})()`,
  );
  await pause();
  assert.equal(await ui("document.hasFocus()"), true);
}
const checks = [];
await ui(`openSettings('shortcuts');true`);
await pause();
await focus();
await ui(
  `openShortcutEditor(shortcuts.find(s=>s.id==='newNote'));startRecording(shortcuts.find(s=>s.id==='newNote'));true`,
);
await pause();
const initial = await count();
execFileSync(keyboard, ["49", "5"]);
await pause();
assert.equal(
  await count(),
  initial,
  "Recording must not trigger the existing app shortcut",
);
assert.equal(await ui("shortcutDraft"), "Ctrl+Shift+N");
checks.push("Recording an existing app shortcut does not execute it");
await ui(`startRecording(shortcuts.find(s=>s.id==='newNote'));true`);
await pause();
execFileSync(keyboard, ["66", "8"]);
await pause();
assert.equal(await ui("shortcutDraft"), "Alt+F8");
checks.push("Recorded Alt+F8 without forced modifiers");
await ui(`saveShortcut(shortcuts.find(s=>s.id==='newNote'));true`);
await pause();
assert.equal(
  await ui(`shortcuts.find(s=>s.id==='newNote').accelerator`),
  "Alt+F8",
);
await focus();
execFileSync(keyboard, ["66", "8"]);
await pause();
assert.equal(await count(), initial + 1);
checks.push("Custom app shortcut executes with its exact modifiers");
await focus();
const duplicate = await ui(
  `window.manager.setShortcut('newNote','Ctrl+Shift+M')`,
);
assert.ok(duplicate.error?.includes("Already assigned"));
checks.push("Duplicate assignment is rejected");
const conflict = await ui(
  `window.manager.setShortcut('newNoteAnywhere','Super+G')`,
);
assert.ok(conflict.error);
assert.equal(
  await ui(
    `window.manager.shortcuts().then(s=>s.find(v=>v.id==='newNoteAnywhere').accelerator)`,
  ),
  "Ctrl+Alt+Shift+J",
);
checks.push("System binding conflict preserves the previous shortcut");
const changed = await ui(
  `window.manager.setShortcut('openManagerAnywhere','Ctrl+Alt+Shift+Space')`,
);
assert.ok(Array.isArray(changed));
checks.push("Global Space combination is accepted");
await evaluate(
  9346,
  "",
  `process.mainModule.require('electron').BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().includes('manager.html')).hide();true`,
);
await pause();
execFileSync(keyboard, ["57", "13"]);
await new Promise((resolve) => setTimeout(resolve, 1000));
assert.equal(
  await evaluate(
    9346,
    "",
    `process.mainModule.require('electron').BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().includes('manager.html')).isVisible()`,
  ),
  true,
);
checks.push("Global Space shortcut opens the hidden manager");
await focus();
await ui(
  `openShortcutEditor(shortcuts.find(s=>s.id==='toggleHideAll'));shortcutDraft='Ctrl+Down';saveShortcut(shortcuts.find(s=>s.id==='toggleHideAll'));true`,
);
await pause();
assert.equal(
  await ui(`shortcuts.find(s=>s.id==='toggleHideAll').accelerator`),
  "Ctrl+Down",
);
checks.push("Manually entered arrow combination saves");
await ui(`window.manager.resetShortcut('newNote');true`);
await pause();
assert.equal(
  await ui(
    `window.manager.shortcuts().then(s=>s.find(v=>v.id==='newNote').accelerator)`,
  ),
  "CommandOrControl+Shift+N",
);
checks.push("Reset restores the original shortcut");
console.log(JSON.stringify({ passed: checks.length, checks }, null, 2));
