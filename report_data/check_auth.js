const { spawn } = require('child_process');
const os = require('os');
const path = require('path');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9464;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_check_auth2_' + Date.now());

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

  await sleep(2000);

  const evalRes = await send('Runtime.evaluate', {
    expression: `
      (async () => {
        const m = await import('/src/services/firebase.ts');
        await m.signInWithEmailAndPassword(m.auth, '123456@gmail.com', '123456');
        return "Signed in!";
      })()
    `,
    returnByValue: true,
    awaitPromise: true
  });
  console.log("Sign in result:", evalRes.result.result.value);

  await sleep(2000);
  const textRes = await send('Runtime.evaluate', {
    expression: 'document.body.innerText',
    returnByValue: true
  });
  console.log("Page text after sign in:\n", textRes.result.result.value.slice(0, 500));

  ws.close();
  chrome.kill();
}

main().catch(console.error);
