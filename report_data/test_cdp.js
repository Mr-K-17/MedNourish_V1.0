const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9222;

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function run() {
  console.log("Launching headless Chrome on port", PORT);
  const chrome = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    '--headless=new',
    '--window-size=1440,900',
    '--disable-gpu',
    'http://localhost:5173/'
  ]);

  chrome.stderr.on('data', d => {});

  let targets = null;
  for (let i = 0; i < 20; i++) {
    await sleep(500);
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await res.json();
      if (targets && targets.length > 0) break;
    } catch (e) {}
  }

  if (!targets || targets.length === 0) {
    console.error("No Chrome target found");
    chrome.kill();
    return;
  }

  console.log("Found page target:", targets[0].title, targets[0].webSocketDebuggerUrl);
  const ws = new WebSocket(targets[0].webSocketDebuggerUrl);

  let id = 1;
  const pending = new Map();

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  };

  await new Promise(r => ws.onopen = r);

  function send(method, params = {}) {
    return new Promise(resolve => {
      const msgId = id++;
      pending.set(msgId, resolve);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  // Wait for initial render
  await sleep(1500);

  // Capture screenshot
  const shotRes = await send('Page.captureScreenshot', { format: 'png' });
  const outPath = path.join(__dirname, 'screenshots', '01_landing_page.png');
  fs.writeFileSync(outPath, Buffer.from(shotRes.result.data, 'base64'));
  console.log("Captured 01_landing_page.png, size:", fs.statSync(outPath).size);

  ws.close();
  chrome.kill();
}

run().catch(console.error);
