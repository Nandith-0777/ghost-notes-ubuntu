import assert from "node:assert/strict";
import { evaluate } from "./cdp.mjs";

const port = Number(process.env.GHOST_NOTES_TEST_PORT || 9345);
const mainPort = Number(process.env.GHOST_NOTES_MAIN_TEST_PORT || 9346);
assert.ok(
  (
    await evaluate(mainPort, "", "process.env.GHOST_NOTES_DATA_DIR")
  )?.startsWith("/tmp/"),
  "Use a disposable app profile",
);
const ui = (expression) => evaluate(port, "manager.html", expression);
const pause = () => new Promise((resolve) => setTimeout(resolve, 120));
const checks = [];
const check = (value, name) => {
  assert.ok(value, name);
  checks.push(name);
};
async function size(width, height) {
  await evaluate(
    mainPort,
    "",
    `(()=>{const w=process.mainModule.require('electron').BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().includes('manager.html'));w.setSize(${width},${height});w.show();w.focus();return true})()`,
  );
  await pause();
  const viewport = await ui("({width:innerWidth,height:innerHeight})");
  assert.equal(
    viewport.width,
    width,
    "Test manager must float so the compositor honors its width",
  );
}
await ui("location.reload();true");
await pause();
for (const [width, height] of [
  [960, 700],
  [560, 420],
]) {
  await size(width, height);
  for (const theme of ["light", "dark"]) {
    await ui(`window.manager.setTheme('${theme}');true`);
    await pause();
    check(
      await ui(
        `(()=>{const els=[document.querySelector('.page-head'),document.querySelector('.note-filters'),...document.querySelectorAll('.card')];return els.every(e=>e.getBoundingClientRect().right<=innerWidth+1)&&document.documentElement.scrollWidth<=innerWidth})()`,
      ),
      `${theme} collection fits ${width}×${height}`,
    );
    await ui(`openWorkspaceForm('create');true`);
    check(
      await ui(
        `(()=>{const r=wsModalEl.getBoundingClientRect();return Math.abs(r.x+r.width/2-innerWidth/2)<=1&&Math.abs(r.y+r.height/2-innerHeight/2)<=1&&r.bottom<=innerHeight&&wsModalEl.contains(document.activeElement)})()`,
      ),
      `Workspace form centered with focus at ${width}, ${theme}`,
    );
    await ui(`document.querySelector('#wsCancel').click();true`);
    await ui(`confirmDeleteWorkspace(activeWorkspace);true`);
    await pause();
    check(
      await ui(
        `(()=>{const r=deleteDialog.getBoundingClientRect();return deleteDialog.open&&Math.abs(r.x+r.width/2-innerWidth/2)<=1&&Math.abs(r.y+r.height/2-innerHeight/2)<=1&&r.bottom<=innerHeight&&document.activeElement.value==='cancel'})()`,
      ),
      `Workspace deletion centered; Cancel focused at ${width}, ${theme}`,
    );
    const before = await ui("workspaces.length");
    await ui(`deleteDialog.querySelector('[value="cancel"]').click();true`);
    await pause();
    check(
      (await ui("workspaces.length")) === before,
      "Cancel leaves workspaces unchanged",
    );
  }
  for (const pane of ["appearance", "shortcuts", "storage", "about"]) {
    await ui(`openSettings('${pane}');true`);
    check(
      await ui(
        `(()=>{const p=document.querySelector('.set-pane');return p.scrollWidth<=p.clientWidth+1&&settingsBodyEl.scrollWidth<=settingsBodyEl.clientWidth+1})()`,
      ),
      `${pane} settings fit ${width}`,
    );
    await ui("closeSettings();true");
  }
}
await ui(`openMoreMenu();true`);
check(
  await ui(`moreMenuEl.contains(document.activeElement)`),
  "Workspace menu receives keyboard focus",
);
await ui(
  `moreMenuEl.dispatchEvent(new KeyboardEvent('keydown',{key:'End',bubbles:true}));true`,
);
check(
  await ui(
    `document.activeElement === [...moreMenuEl.querySelectorAll('button:not(:disabled)')].at(-1)`,
  ),
  "Menu End key selects last action",
);
await ui(
  `document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));true`,
);
check(
  await ui(`moreMenuEl.hidden && document.activeElement === moreBtnEl`),
  "Menu Escape restores focus",
);
await size(960, 700);
await ui(`document.querySelector('[data-filter="open"]').click();true`);
check(
  await ui(
    `document.querySelectorAll('.card').length === notesForList().filter(n=>n.visible).length`,
  ),
  "On desktop filter",
);
await ui(`document.querySelector('[data-filter="hidden"]').click();true`);
check(
  await ui(
    `document.querySelectorAll('.card').length === notesForList().filter(n=>!n.visible).length`,
  ),
  "Hidden filter",
);
await ui(
  `document.querySelector('[data-filter="all"]').click();searchEl.value='no matching note 123456';searchEl.dispatchEvent(new Event('input'));true`,
);
check(
  await ui(
    `document.querySelectorAll('.card').length===0&&!!document.querySelector('.empty')`,
  ),
  "Search empty state",
);
await ui(
  `searchEl.value='';searchEl.dispatchEvent(new Event('input'));openWorkspaceForm('create');wsNameInputEl.value='Deletion test';wsFormEl.requestSubmit();true`,
);
await pause();
const id = await ui(`workspaces.find(w=>w.name==='Deletion test')?.id`);
assert.ok(id);
await ui(`selectScope(${JSON.stringify(id)});window.manager.newNote();true`);
await pause();
const note = await ui(`notes.find(n=>n.workspaceId===${JSON.stringify(id)})`);
assert.ok(note);
await ui(`confirmDeleteWorkspace(${JSON.stringify(id)});true`);
await pause();
check(
  await ui(
    `document.querySelector('#deleteDescription').textContent.includes('Your notes will be kept')`,
  ),
  "Workspace deletion explains that notes are kept",
);
await ui(`document.querySelector('#deleteConfirm').click();true`);
await pause();
check(
  await ui(
    `!workspaces.some(w=>w.id===${JSON.stringify(id)})&&notes.some(n=>n.id===${JSON.stringify(note.id)}&&n.workspaceId!==${JSON.stringify(id)})`,
  ),
  "Confirmed workspace deletion moves notes instead of deleting them",
);
await ui(`confirmDeleteNote(${JSON.stringify(note.id)});true`);
await ui(`deleteDialog.querySelector('[value="cancel"]').click();true`);
await pause();
check(
  await ui(`notes.some(n=>n.id===${JSON.stringify(note.id)})`),
  "Cancel leaves note unchanged",
);
await ui(`confirmDeleteNote(${JSON.stringify(note.id)});true`);
await ui(`document.querySelector('#deleteConfirm').click();true`);
await pause();
check(
  await ui(`!notes.some(n=>n.id===${JSON.stringify(note.id)})`),
  "Confirmed note deletion",
);
await ui(`window.manager.setTheme('light');true`);
console.log(JSON.stringify({ passed: checks.length, checks }, null, 2));
