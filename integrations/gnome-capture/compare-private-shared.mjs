import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import { evaluate } from "../../scripts/cdp.mjs";
assert.equal(
  os.userInfo().username,
  "ghostdev",
  "Run only in the Ubuntu test VM",
);
const root = path.join(os.homedir(), "ghost-notes-gnome");
const stock = process.argv.includes("--expect-stock");
const output = path.join(
  root,
  "validation",
  stock ? "stock-control" : "prototype",
);
const ev = (code) => evaluate(9342, "note.html", code);
const wait = () => new Promise((resolve) => setTimeout(resolve, 600));
const capture = (name) => {
  for (const region of [false, true]) {
    JSON.parse(
      execFileSync(
        "python3",
        [
          path.join(root, "capture-frame.py"),
          path.join(output, name + (region ? "-area" : "") + ".png"),
          ...(region ? ["--region", "400", "300", "360", "220"] : []),
        ],
        { encoding: "utf8", timeout: 30000 },
      ),
    );
  }
};
let ready = false;
for (let attempt = 0; attempt < 60; attempt++) {
  try {
    ready = await ev(
      "typeof state !== 'undefined' && state.text === 'PRIVATE CAPTURE TEST NOTE'",
    );
    if (ready) break;
  } catch {}
  await wait();
}
assert.ok(
  ready,
  "The isolated note must finish startup before capture testing",
);
assert.equal(await ev("state.text"), "PRIVATE CAPTURE TEST NOTE");
assert.equal(await ev("state.shareVisible"), false);
assert.equal(
  await ev("window.notes.getState(id).then(record=>record.visible)"),
  true,
  "The synthetic note must be locally visible before testing exclusion",
);
const appCapture = await ev(
  "window.notes.runtime().then(runtime=>runtime.capture)",
);
assert.equal(appCapture.mode, stock ? "unsupported" : "compositor-omit");
if (!stock) assert.equal(appCapture.provider, "gnome-mutter");
await wait();
capture("private");
await ev('document.getElementById("shareVisibility").click()');
await wait();
assert.equal(await ev("state.shareVisible"), true);
capture("shared");
await ev('document.getElementById("shareVisibility").click()');
await wait();
assert.equal(await ev("state.shareVisible"), false);
capture("private-again");
await ev("window.notes.close(id)");
await wait();
capture("baseline");
const code = String.raw`
from pathlib import Path
import json,sys,gi
gi.require_version('GdkPixbuf','2.0')
from gi.repository import GdkPixbuf
root=Path(sys.argv[1]);images={name:GdkPixbuf.Pixbuf.new_from_file(str(root/(name+'.png'))) for name in ['private','shared','private-again','baseline']}
x,y,width,height=400,300,360,220
def pixels(image):
 channels=image.get_n_channels();stride=image.get_rowstride();data=image.get_pixels()
 return [bytes(data[(y+r)*stride+(x+c)*channels:(y+r)*stride+(x+c+1)*channels]) for r in range(height) for c in range(width)]
reference=pixels(images['baseline'])
result={name:sum(a!=b for a,b in zip(pixels(image),reference)) for name,image in images.items() if name!='baseline'}
area={name:GdkPixbuf.Pixbuf.new_from_file(str(root/(name+'-area.png'))) for name in ['private','shared','private-again','baseline']}
def area_pixels(image):
 channels=image.get_n_channels();stride=image.get_rowstride();data=image.get_pixels()
 return [bytes(data[r*stride+c*channels:r*stride+(c+1)*channels]) for r in range(image.get_height()) for c in range(image.get_width())]
area_reference=area_pixels(area['baseline'])
result['area']={name:sum(a!=b for a,b in zip(area_pixels(image),area_reference)) for name,image in area.items() if name!='baseline'}
print(json.dumps(result))
`;
const differences = JSON.parse(
  execFileSync("python3", ["-c", code, output], { encoding: "utf8" }),
);
for (const stream of [differences, differences.area]) {
  if (stock) {
    assert.ok(
      stream.private > 1000,
      "Stock Ubuntu must demonstrate the missing exclusion",
    );
    assert.ok(stream["private-again"] > 1000);
  } else {
    assert.equal(
      stream.private,
      0,
      "Private capture must match the live background exactly",
    );
    assert.equal(stream["private-again"], 0);
  }
  assert.ok(stream.shared > 1000, "Explicitly shared notes must appear");
}
const report = {
  backend: "Mutter ScreenCast / PipeWire",
  stockControl: stock,
  appCapture,
  region: { x: 400, y: 300, width: 360, height: 220 },
  differentPixelsFromBackground: differences,
  privateExcluded: differences.private === 0,
  sharedVisible: true,
  privateAgainExcluded: differences["private-again"] === 0,
};
fs.writeFileSync(
  path.join(output, "capture-validation.json"),
  JSON.stringify(report, null, 2) + "\n",
);
console.log(JSON.stringify(report));
