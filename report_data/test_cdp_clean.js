const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9444;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_cdp_test_' + Date.now());

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function run() {
  console.log("Launching headless Chrome on port", PORT, "dir:", USER_DATA_DIR);
  const chrome = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    '--headless=new',
    '--window-size=1440,900',
    '--disable-gpu',
    'http://localhost:5173/'
  ]);

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
    console.error("No targets found");
    chrome.kill();
    return;
  }

  const pageTarget = targets.find(t => t.type === 'page') || targets[0];
  console.log("Found page target:", pageTarget.title, pageTarget.url, pageTarget.webSocketDebuggerUrl);

  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
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

  // Wait for React app to mount
  await sleep(2500);

  // Take screenshot
  const shotRes = await send('Page.captureScreenshot', { format: 'png' });
  const outPath = path.join(__dirname, 'screenshots', '01_landing_page.png');
  fs.writeFileSync(outPath, Buffer.from(shotRes.result.data, 'base64'));
  console.log("SUCCESS! Captured 01_landing_page.png, bytes:", fs.statSync(outPath).size);

  ws.close();
  chrome.kill();
}

run().catch(console.error);
