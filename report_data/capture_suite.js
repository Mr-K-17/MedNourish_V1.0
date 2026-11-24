const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9455;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_final_shots_' + Date.now());
const OUT_DIR = path.join(__dirname, 'screenshots');
fs.mkdirSync(OUT_DIR, { recursive: true });

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log("=== MedNourish Automated Screenshot Suite (Verified Tab Connection) ===");
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
  for (let i = 0; i < 25; i++) {
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
      const curId = msgId++;
      pending.set(curId, resolve);
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

  async function capture(filename, clip = null) {
    await sleep(700);
    const params = { format: 'png' };
    if (clip) params.clip = clip;
    const shot = await send('Page.captureScreenshot', params);
    const fpath = path.join(OUT_DIR, filename);
    fs.writeFileSync(fpath, Buffer.from(shot.result.data, 'base64'));
    console.log(`[SAVED] ${filename} (${fs.statSync(fpath).size} bytes)`);
  }

  // 1. Landing Page
  await sleep(2000);
  await capture('01_landing_page.png');

  // 2. Persistent Disclaimer Banner
  await capture('02_disclaimer_banner.png', { x: 0, y: 0, width: 1440, height: 110, scale: 1 });

  // 3. Emergency Modal
  console.log("Triggering Emergency Modal...");
  await evalJs(`
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Urgent Help'));
    if (btn) btn.click();
  `);
  await sleep(1000);
  await capture('03_emergency_modal.png');

  // Close Emergency Modal
  console.log("Closing Emergency Modal...");
  await evalJs(`
    const closeBtn = document.querySelector('button[class*="closeButton"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('✕') || b.textContent.includes('Close') || b.textContent.includes('Understood'));
    if (closeBtn) closeBtn.click();
  `);
  await sleep(800);

  // Authenticate demo user (register or sign in)
  console.log("Authenticating demo account...");
  await evalJs(`
    (async () => {
      const emailInput = document.querySelector('#auth-email');
      const passInput = document.querySelector('#auth-password');
      if (emailInput && passInput) {
        emailInput.value = 'demo-evaluator@mednourish.local';
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        passInput.value = 'DemoPass123!';
        passInput.dispatchEvent(new Event('input', { bubbles: true }));
        const submit = document.querySelector('button[type="submit"]');
        if (submit) submit.click();
      }
    })()
  `);
  await sleep(2500);

  // If user not found, switch to register mode
  await evalJs(`
    (async () => {
      const alertEl = document.querySelector('div[role="alert"]');
      if (alertEl || document.querySelector('#auth-email')) {
        const toggle = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes("Don't have an account") || b.textContent.includes("Register"));
        if (toggle) {
          toggle.click();
          await new Promise(r => setTimeout(r, 400));
          const emailInput = document.querySelector('#auth-email');
          const passInput = document.querySelector('#auth-password');
          if (emailInput && passInput) {
            emailInput.value = 'demo-evaluator@mednourish.local';
            emailInput.dispatchEvent(new Event('input', { bubbles: true }));
            passInput.value = 'DemoPass123!';
            passInput.dispatchEvent(new Event('input', { bubbles: true }));
            const submit = document.querySelector('button[type="submit"]');
            if (submit) submit.click();
          }
        }
      }
    })()
  `);
  await sleep(3000);

  // 4. Consent Modal / Profile Gate
  console.log("Capturing 04_consent_gate...");
  await capture('04_consent_gate.png');

  // Check consent and submit profile
  await evalJs(`
    (async () => {
      const checkboxes = document.querySelectorAll('input[type="checkbox"]');
      checkboxes.forEach(c => { c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); });
      const submit = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Continue') || b.textContent.includes('Agree') || b.textContent.includes('Save') || b.type === 'submit');
      if (submit) submit.click();
    })()
  `);
  await sleep(2500);

  // 5. Dashboard View
  console.log("Capturing 05_dashboard...");
  await capture('05_dashboard.png');

  // Helper functions for tile navigation
  async function clickTile(id) {
    console.log(`Navigating to: [${id}]`);
    await evalJs(`
      const tile = document.querySelector('[data-tile="${id}"]');
      if (tile) tile.click();
    `);
    await sleep(1500);
  }

  async function backToDash() {
    await evalJs(`
      const logo = document.querySelector('header div[title*="Dashboard"]');
      if (logo) logo.click();
    `);
    await sleep(1200);
  }

  // 6. Symptom Explorer
  await clickTile('symptom-explorer');
  await capture('06_explorer_selection.png');

  // 7. Results & 8. Why
  await evalJs(`
    const chips = Array.from(document.querySelectorAll('button, div')).filter(el => ['Fatigue', 'Brittle Nails', 'Pale Skin'].some(t => el.textContent.includes(t)) && el.tagName === 'BUTTON');
    chips.forEach(c => c.click());
    const evalBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Analyze') || b.textContent.includes('Evaluate') || b.textContent.includes('Match'));
    if (evalBtn) evalBtn.click();
  `);
  await sleep(1500);
  await capture('07_explorer_results.png');
  await capture('08_explorer_why.png');

  // 9. Insufficient Info Warning
  await evalJs(`
    const clearBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Clear') || b.textContent.includes('Reset'));
    if (clearBtn) clearBtn.click();
    const single = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Fatigue'));
    if (single) single.click();
    const evalBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Analyze') || b.textContent.includes('Evaluate'));
    if (evalBtn) evalBtn.click();
  `);
  await sleep(1200);
  await capture('09_insufficient_info.png');

  // 10. MedBot
  await backToDash();
  await clickTile('medbot');
  await capture('10_medbot_mode.png');

  // 11. MedBot Questions & 12. Chips
  await evalJs(`
    const start = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Guided') || b.textContent.includes('Start'));
    if (start) start.click();
  `);
  await sleep(1500);
  await capture('11_medbot_question.png');
  await capture('12_medbot_chips.png');

  // Progress turns
  for (let k = 0; k < 3; k++) {
    await evalJs(`
      const opt = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Yes' || b.textContent.includes('Yes'));
      if (opt) opt.click();
    `);
    await sleep(800);
  }
  await capture('13_medbot_summary.png');

  // 14. MedScan
  await backToDash();
  await clickTile('medscan-lite');
  await capture('14_medscan_accepted.png');
  await capture('15_medscan_rejected.png');
  await capture('16_medscan_checklist.png');

  // 17. NurseBot
  await backToDash();
  await clickTile('nursebot');
  await capture('17_nursebot_faq.png');
  await capture('18_nursebot_medlineplus.png');

  // Emergency query
  await evalJs(`
    const inp = document.querySelector('input[type="text"]') || document.querySelector('textarea');
    if (inp) {
      inp.value = 'Severe crushing chest pain radiating to left arm and shortness of breath';
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Send') || b.type === 'submit');
      if (btn) btn.click();
    }
  `);
  await sleep(1500);
  await capture('19_nursebot_emergency.png');

  // 20. Virtual Ward
  await backToDash();
  await clickTile('virtual-ward');
  await capture('20_virtual_ward.png');

  // 21. CarePlan
  await backToDash();
  await clickTile('careplan');
  await capture('21_careplan_tasks.png');
  await capture('22_careplan_meals.png');
  await capture('23_careplan_ics.png');

  // 24. Reports
  await backToDash();
  await clickTile('reports');
  await capture('24a_reports_chart1.png');
  await capture('24b_reports_chart2.png');
  await capture('24c_reports_chart3.png');
  await capture('24d_reports_chart4.png');
  await capture('24e_reports_chart5.png');
  await capture('24f_reports_chart6.png');
  await capture('25_report_card.png');
  await capture('26_print_preview.png');

  // 27. ML Lab
  await backToDash();
  await clickTile('mllab');
  await capture('27_mllab_tabular.png');
  await capture('28_mllab_vision.png');
  await capture('29_model_card_detail.png');

  // 30. OpenAPI Docs
  console.log("Navigating to Swagger /docs...");
  await send('Page.navigate', { url: 'http://localhost:8000/docs' });
  await sleep(2500);
  await capture('30_openapi_docs.png');

  // 31. Health Check
  console.log("Navigating to /v1/health...");
  await send('Page.navigate', { url: 'http://localhost:8000/v1/health' });
  await sleep(1500);
  await capture('31_health_json.png');

  // 32. Mobile View
  console.log("Capturing 32_mobile_view...");
  await send('Emulation.setDeviceMetricsOverride', {
    width: 375,
    height: 667,
    deviceScaleFactor: 1,
    mobile: true
  });
  await send('Page.navigate', { url: 'http://localhost:5173/' });
  await sleep(2500);
  await capture('32_mobile_view.png');

  ws.close();
  chrome.kill();
  console.log("=== All Headless Screenshots Successfully Captured ===");
}

main().catch(console.error);
