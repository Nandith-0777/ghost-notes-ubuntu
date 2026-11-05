import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { evaluate } from "./cdp.mjs";

assert.ok(
  process.env.GHOST_NOTES_DATA_DIR?.startsWith("/tmp/"),
  "Use a disposable test profile",
);
const hy = (...args) =>
  execFileSync("hyprctl", args, { encoding: "utf8", timeout: 5000 });
const note = (expression) => evaluate(9342, "note.html", expression);
const fixture = (expression) => evaluate(9343, "data:text/html", expression);
const wait = () => new Promise((r) => setTimeout(r, 300));
const clients = JSON.parse(hy("clients", "-j"));
const win = clients.find((w) => w.title === "Ghost Notes Note");
assert.ok(win);
assert.equal(
  clients.filter((w) => w.title === "Ghost Notes Note").length,
  1,
  "Use exactly one disposable note so another note cannot intercept the body click",
);
for (const w of clients.filter((w) =>
  ["Ghost Notes Note", "Public capture fixture"].includes(w.title),
)) {
  hy(
    "dispatch",
    `hl.dsp.window.move({workspace="2",follow=false,window="address:${w.address}"})`,
  );
}
await wait();
const current = JSON.parse(hy("clients", "-j")).find(
  (w) => w.address === win.address,
);
const monitors = JSON.parse(hy("monitors", "-j"));
const left = Math.min(...monitors.map((m) => m.x));
const top = Math.min(...monitors.map((m) => m.y));
const width = Math.max(
  ...monitors.map(
    (m) => m.x + (m.transform % 2 ? m.height : m.width) / m.scale,
  ),
);
const height = Math.max(
  ...monitors.map(
    (m) => m.y + (m.transform % 2 ? m.width : m.height) / m.scale,
  ),
);
const pointer = process.env.GHOST_NOTES_TEST_POINTER;
assert.ok(
  pointer?.startsWith("/tmp/"),
  "Supply the disposable virtual-pointer test client",
);
let position;
const move = (x, y) => {
  position = [Math.round(x), Math.round(y)];
  execFileSync(
    pointer,
    [position[0] - left, position[1] - top, width - left, height - top, 0].map(
      String,
    ),
  );
};
const click = () => {
  execFileSync(
    pointer,
    [position[0] - left, position[1] - top, width - left, height - top, 1].map(
      String,
    ),
  );
};
await fixture(
  `(() => {
    document.body.replaceChildren();
    window.testClicks = 0;
    const button = document.createElement("button");
    button.style.cssText = "position:fixed;inset:0;font-size:32px";
    button.textContent = "Public test button";
    button.onclick = () => { window.testClicks++; button.textContent = "Clicks: " + window.testClicks; };
    document.body.append(button);
  })()`,
);
await note("if(!state.ghost) document.querySelector('#ghost').click()");
try {
  move(current.at[0] + 80, current.at[1] + 100);
  await wait();
  assert.equal(await note("ignoring"), true);
  click();
  await wait();
  assert.ok(
    (await fixture("window.testClicks")) > 0,
    "Body click must reach the application behind the note",
  );
  const bar = await note(
    "(()=>{const b=document.querySelector('#ghost').getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2,width:innerWidth,height:innerHeight}})()",
  );
  const barX = current.at[0] + (bar.x * current.size[0]) / bar.width;
  const barY = current.at[1] + (bar.y * current.size[1]) / bar.height;
  move(barX, barY);
  await wait();
  assert.equal(
    await note("ignoring"),
    false,
    "Hovering toolbar must recover input on Linux",
  );
  const previousClicks = await fixture("window.testClicks");
  move(current.at[0] + 80, current.at[1] + 100);
  click();
  await wait();
  assert.ok(
    (await fixture("window.testClicks")) > previousClicks,
    "Body clicks must still pass through after toolbar recovery",
  );
  move(barX, barY);
  await wait();
  assert.equal(await note("ignoring"), false);
  move(barX + 1, barY);
  await wait();
  click();
  await wait();
  assert.equal(
    await note("state.ghost"),
    false,
    "Compositor click must disable ghost mode",
  );
  console.log(
    "PASS: body click-through, toolbar hover recovery, and compositor click to exit ghost mode",
  );
} finally {
  await note("if(state.ghost) document.querySelector('#ghost').click()");
}
