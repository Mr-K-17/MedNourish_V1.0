const { spawn } = require('child_process');
const os = require('os');
const path = require('path');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9461;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_test_cors_' + Date.now());

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const chrome = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    '--headless=new',
    '--disable-extensions',
    '--disable-web-security',
    '--window-size=1440,900',
    '--disable-gpu',
    'http://127.0.0.1:5173/'
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
  console.log("Attached to Web App:", page.url);

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let msgId = 1;
  const pending = new Map();
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  };
  await new Promise(r => ws.onopen = r);

  function send(method, params = {}) {
    return new Promise(r => {
      const curId = msgId++;
      pending.set(curId, r);
      ws.send(JSON.stringify({ id: curId, method, params }));
    });
  }

  async function evalJs(code) {
    const res = await send('Runtime.evaluate', {
      expression: code,
      returnByValue: true,
      awaitPromise: true
    });
    return (res.result && res.result.result) ? res.result.result.value : null;
  }

  await sleep(2000);

  // Fill credentials and click Sign In
  const loginRes = await evalJs(`
    (async () => {
      const emailInput = document.querySelector('#auth-email');
      const passInput = document.querySelector('#auth-password');
      if (!emailInput || !passInput) return 'Inputs not found';
      
      emailInput.value = '123456@gmail.com';
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));

      passInput.value = '123456';
      passInput.dispatchEvent(new Event('input', { bubbles: true }));

      const submitBtn = document.querySelector('button[type="submit"]');
      if (!submitBtn) return 'Submit button not found';
      submitBtn.click();
      return 'Clicked submit';
    })()
  `);
  console.log("Login action result:", loginRes);

  for (let s = 1; s <= 6; s++) {
    await sleep(1000);
    const bodyText = await evalJs('document.body.innerText');
    console.log(`[After ${s}s] Page text preview:\n`, bodyText ? bodyText.slice(0, 300).replace(/\\n+/g, ' | ') : 'null');
    if (bodyText && bodyText.includes('Clinical Suite')) {
      console.log("SUCCESSFULLY ENTERED DASHBOARD!");
      break;
    }
  }

  ws.close();
  chrome.kill();
}

main().catch(console.error);
