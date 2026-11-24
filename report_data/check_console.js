const { spawn } = require('child_process');
const os = require('os');
const path = require('path');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9462;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_check_console_' + Date.now());

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
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let msgId = 1;
  const pending = new Map();
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.method === 'Runtime.consoleAPICalled') {
      console.log("[CONSOLE]", m.params.type, m.params.args.map(a => a.value || a.description || JSON.stringify(a)).join(' '));
    } else if (m.method === 'Runtime.exceptionThrown') {
      console.log("[EXCEPTION]", m.params.exceptionDetails.text, m.params.exceptionDetails.exception?.description);
    }
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

  await send('Runtime.enable');
  await send('Log.enable');
  await sleep(1500);

  // Directly call signInWithEmailAndPassword inside the browser!
  const res = await send('Runtime.evaluate', {
    expression: `
      (async () => {
        try {
          // Find inputs
          const emailInput = document.querySelector('#auth-email');
          const passInput = document.querySelector('#auth-password');
          emailInput.value = '123456@gmail.com';
          emailInput.dispatchEvent(new Event('input', { bubbles: true }));
          passInput.value = '123456';
          passInput.dispatchEvent(new Event('input', { bubbles: true }));
          
          document.querySelector('button[type="submit"]').click();
          return "Submitted";
        } catch(e) {
          return "Err: " + e.message;
        }
      })()
    `,
    returnByValue: true,
    awaitPromise: true
  });
  console.log("Evaluate result:", res.result.result.value);

  await sleep(3000);
  ws.close();
  chrome.kill();
}

main().catch(console.error);
