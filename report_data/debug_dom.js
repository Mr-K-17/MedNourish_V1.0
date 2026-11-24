const { spawn } = require('child_process');
const os = require('os');
const path = require('path');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9452;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_debug6_' + Date.now());

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const chrome = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    '--headless=new',
    '--disable-extensions',
    '--window-size=1440,900',
    '--disable-gpu',
    'http://localhost:5173/'
  ]);

  let targets = null;
  for (let i = 0; i < 20; i++) {
    await sleep(400);
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await res.json();
      if (targets && targets.some(t => t.url.includes('5173'))) break;
    } catch (e) {}
  }

  const page = targets.find(t => t.url.includes('5173')) || targets[0];
  console.log("Found real tab:", page.url);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 1;
  const pending = new Map();
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  };
  await new Promise(r => ws.onopen = r);

  function send(method, params = {}) {
    return new Promise(r => { const mid = id++; pending.set(mid, r); ws.send(JSON.stringify({ id: mid, method, params })); });
  }

  await sleep(2500);
  const evalRes = await send('Runtime.evaluate', {
    expression: `
      (() => {
        return {
          title: document.title,
          h1: Array.from(document.querySelectorAll('h1, h2, h3, h4')).map(e => e.textContent),
          buttons: Array.from(document.querySelectorAll('button')).map(e => e.textContent.trim())
        };
      })()
    `,
    returnByValue: true
  });
  console.log("REAL PAGE DATA:\n", JSON.stringify(evalRes.result.result.value, null, 2));

  ws.close();
  chrome.kill();
}
main().catch(console.error);
