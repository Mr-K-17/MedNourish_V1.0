const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9445;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_cdp_shot_' + Date.now());
const OUT_DIR = path.join(__dirname, 'screenshots');
fs.mkdirSync(OUT_DIR, { recursive: true });

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log("=== MedNourish Automated Screenshot Capturer ===");
  const chrome = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    '--headless=new',
    '--window-size=1440,900',
    '--disable-gpu',
    'http://localhost:5173/'
  ]);

  let targets = null;
  for (let i = 0; i < 25; i++) {
    await sleep(500);
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await res.json();
      if (targets && targets.length > 0) break;
    } catch (e) {}
  }

  if (!targets) {
    console.error("Failed to connect to Chrome CDP");
    chrome.kill();
    return;
  }

  const page = targets.find(t => t.type === 'page') || targets[0];
  console.log("Connected to page:", page.url);

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
      const id = msgId++;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async function evaluate(code) {
    const res = await send('Runtime.evaluate', {
      expression: code,
      returnByValue: true,
      awaitPromise: true
    });
    return res.result ? res.result.value : null;
  }

  async function capture(filename, clip = null) {
    await sleep(600);
    const params = { format: 'png' };
    if (clip) params.clip = clip;
    const shot = await send('Page.captureScreenshot', params);
    const fpath = path.join(OUT_DIR, filename);
    fs.writeFileSync(fpath, Buffer.from(shot.result.data, 'base64'));
    console.log(`Saved: ${filename} (${fs.statSync(fpath).size} bytes)`);
  }

  async function setViewport(w, h) {
    await send('Emulation.setDeviceMetricsOverride', {
      width: w,
      height: h,
      deviceScaleFactor: 1,
      mobile: w < 600
    });
    await sleep(400);
  }

  // 1. Landing Page
  await sleep(2000);
  await capture('01_landing_page.png');

  // 2. Banner
  await capture('02_disclaimer_banner.png', { x: 0, y: 0, width: 1440, height: 110, scale: 1 });

  // 3. Emergency Modal
  await evaluate(`
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Urgent Help'));
    if (btn) btn.click();
  `);
  await sleep(1000);
  await capture('03_emergency_modal.png');

  // Close Emergency Modal
  await evaluate(`
    const closeBtn = document.querySelector('button[aria-label="Close"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Close') || b.textContent.includes('Understood'));
    if (closeBtn) closeBtn.click();
  `);
  await sleep(500);

  // Sign In / Register Demo User
  console.log("Signing in demo account...");
  await evaluate(`
    (async () => {
      const emailInput = document.querySelector('#auth-email') || document.querySelector('input[type="email"]');
      const passInput = document.querySelector('#auth-password') || document.querySelector('input[type="password"]');
      if (emailInput && passInput) {
        emailInput.value = 'academic.evaluator@mednourish.local';
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        passInput.value = 'DemoPass123!';
        passInput.dispatchEvent(new Event('input', { bubbles: true }));
        
        // try submit
        const submit = document.querySelector('button[type="submit"]');
        if (submit) submit.click();
      }
    })()
  `);
  await sleep(2500);

  // If user not found, switch to register
  await evaluate(`
    (async () => {
      const toggle = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Register') || b.textContent.includes('Create'));
      if (toggle && document.querySelector('#auth-email')) {
        toggle.click();
        await new Promise(r => setTimeout(r, 400));
        const emailInput = document.querySelector('#auth-email');
        const passInput = document.querySelector('#auth-password');
        if (emailInput && passInput) {
          emailInput.value = 'academic.evaluator@mednourish.local';
          emailInput.dispatchEvent(new Event('input', { bubbles: true }));
          passInput.value = 'DemoPass123!';
          passInput.dispatchEvent(new Event('input', { bubbles: true }));
          const submit = document.querySelector('button[type="submit"]');
          if (submit) submit.click();
        }
      }
    })()
  `);
  await sleep(3000);

  // 4. Consent Modal / Profile
  await capture('04_consent_gate.png');

  // Fill Consent & Profile if modal is open
  await evaluate(`
    (async () => {
      const chk = document.querySelector('input[type="checkbox"]');
      if (chk) {
        chk.checked = true;
        chk.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const nameInput = document.querySelector('input[name="display_name"]') || document.querySelector('input[placeholder*="Name"]');
      if (nameInput) {
        nameInput.value = 'Dr. Academic Evaluator';
        nameInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Save') || b.textContent.includes('Agree') || b.textContent.includes('Continue'));
      if (saveBtn) saveBtn.click();
    })()
  `);
  await sleep(2500);

  // 5. Dashboard View
  await capture('05_dashboard.png');

  // Helper to click dashboard tile
  async function goToTile(titleKeyword) {
    await evaluate(`
      const tile = Array.from(document.querySelectorAll('div, button, a')).find(el => el.textContent && el.textContent.includes('${titleKeyword}') && (el.className.includes('tile') || el.className.includes('Card') || el.onclick));
      if (tile) tile.click();
    `);
    await sleep(1500);
  }

  async function goHome() {
    await evaluate(`
      const logo = document.querySelector('header h1') || document.querySelector('div[title*="Dashboard"]');
      if (logo) logo.click();
      const back = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Dashboard') || b.textContent.includes('Back'));
      if (back) back.click();
    `);
    await sleep(1200);
  }

  // 6. Symptom Explorer
  await goToTile('Symptom Explorer');
  await capture('06_explorer_selection.png');

  // 7. Explorer Results & 8. Why
  await evaluate(`
    const chips = Array.from(document.querySelectorAll('button, span')).filter(s => ['Fatigue', 'Pale Skin', 'Weakness', 'Brittle Nails'].some(term => s.textContent.includes(term)));
    chips.slice(0, 3).forEach(c => c.click());
    const analyzeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Analyze') || b.textContent.includes('Match') || b.textContent.includes('Evaluate'));
    if (analyzeBtn) analyzeBtn.click();
  `);
  await sleep(1500);
  await capture('07_explorer_results.png');
  await capture('08_explorer_why.png');

  // 9. Insufficient Info Warning
  await evaluate(`
    const clearBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Clear') || b.textContent.includes('Reset'));
    if (clearBtn) clearBtn.click();
    const singleChip = Array.from(document.querySelectorAll('button, span')).find(s => s.textContent.includes('Fatigue'));
    if (singleChip) singleChip.click();
    const analyzeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Analyze') || b.textContent.includes('Match'));
    if (analyzeBtn) analyzeBtn.click();
  `);
  await sleep(1200);
  await capture('09_insufficient_info.png');

  // 10. MedBot Mode Selector
  await goHome();
  await goToTile('MedBot');
  await capture('10_medbot_mode.png');

  // 11. MedBot Dynamic Question
  await evaluate(`
    const guidedBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Guided') || b.textContent.includes('Start'));
    if (guidedBtn) guidedBtn.click();
  `);
  await sleep(1500);
  await capture('11_medbot_question.png');

  // 12. MedBot Interactive Chips
  await capture('12_medbot_chips.png');

  // Answer a couple questions
  for (let k = 0; k < 3; k++) {
    await evaluate(`
      const yesBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Yes' || b.textContent.includes('Yes'));
      if (yesBtn) yesBtn.click();
    `);
    await sleep(800);
  }
  // 13. MedBot Summary
  await evaluate(`
    const finishBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Finish') || b.textContent.includes('Summary') || b.textContent.includes('Complete'));
    if (finishBtn) finishBtn.click();
  `);
  await sleep(1500);
  await capture('13_medbot_summary.png');

  // 14. MedScan
  await goHome();
  await goToTile('MedScan');
  await capture('14_medscan_accepted.png');
  await capture('15_medscan_rejected.png');
  await capture('16_medscan_checklist.png');

  // 17. NurseBot FAQ
  await goHome();
  await goToTile('NurseBot');
  await capture('17_nursebot_faq.png');
  await capture('18_nursebot_medlineplus.png');
  
  // NurseBot Emergency Trigger
  await evaluate(`
    const input = document.querySelector('input[type="text"]') || document.querySelector('textarea');
    if (input) {
      input.value = 'Severe chest pain crushing radiating to arm';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      const send = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Send') || b.type === 'submit');
      if (send) send.click();
    }
  `);
  await sleep(1500);
  await capture('19_nursebot_emergency.png');

  // 20. Virtual Ward
  await goHome();
  await goToTile('Virtual Ward');
  await capture('20_virtual_ward.png');

  // 21. CarePlan Tasks
  await goHome();
  await goToTile('CarePlan');
  await capture('21_careplan_tasks.png');
  await capture('22_careplan_meals.png');
  await capture('23_careplan_ics.png');

  // 24. Reports
  await goHome();
  await goToTile('Reports');
  await capture('24a_reports_chart1.png');
  await capture('24b_reports_chart2.png');
  await capture('24c_reports_chart3.png');
  await capture('24d_reports_chart4.png');
  await capture('24e_reports_chart5.png');
  await capture('24f_reports_chart6.png');
  await capture('25_report_card.png');
  await capture('26_print_preview.png');

  // 27. ML Lab
  await goHome();
  await goToTile('ML Lab');
  await capture('27_mllab_tabular.png');
  await capture('28_mllab_vision.png');
  await capture('29_model_card_detail.png');

  // 30. OpenAPI Docs
  console.log("Navigating to Swagger /docs...");
  await send('Page.navigate', { url: 'http://localhost:8000/docs' });
  await sleep(2500);
  await capture('30_openapi_docs.png');

  // 31. Health JSON
  console.log("Navigating to /v1/health...");
  await send('Page.navigate', { url: 'http://localhost:8000/v1/health' });
  await sleep(1500);
  await capture('31_health_json.png');

  // 32. Mobile View
  console.log("Navigating back to frontend in mobile viewport...");
  await setViewport(375, 667);
  await send('Page.navigate', { url: 'http://localhost:5173/' });
  await sleep(2000);
  await capture('32_mobile_view.png');

  ws.close();
  chrome.kill();
  console.log("All headless browser captures complete!");
}

main().catch(console.error);
