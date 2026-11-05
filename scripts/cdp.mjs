import assert from "node:assert/strict";

export async function evaluate(port, match, expression) {
  const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = pages.find((p) => p.url.includes(match));
  assert.ok(page, `Renderer not found: ${match}`);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error("Renderer request timed out"));
    }, 10000);
    ws.addEventListener("message", (event) => {
      const response = JSON.parse(event.data);
      if (response.id !== 1) return;
      clearTimeout(timer);
      ws.close();
      if (response.error || response.result?.exceptionDetails)
        reject(new Error(JSON.stringify(response)));
      else resolve(response.result?.result?.value);
    });
    ws.send(
      JSON.stringify({
        id: 1,
        method: "Runtime.evaluate",
        params: {
          expression,
          awaitPromise: true,
          returnByValue: true,
        },
      }),
    );
  });
}
