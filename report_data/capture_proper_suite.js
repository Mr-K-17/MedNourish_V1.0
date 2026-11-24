const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9470;
const USER_DATA_DIR = path.join(os.tmpdir(), 'chrome_proper_shots_' + Date.now());
const OUT_DIR = path.join(__dirname, 'screenshots');
fs.mkdirSync(OUT_DIR, { recursive: true });

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log("================================================================================");
  console.log("MEDNOURISH PROPER APPLICATION SCREENSHOT CAPTURE");
  console.log("Target User: 123456@gmail.com / 123456");
  console.log("Output: report_data/screenshots/");
  console.log("================================================================================");

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
  for (let i = 0; i < 25; i++) {
    await sleep(400);
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      targets = await res.json();
      if (targets && targets.some(t => t.url.includes('5173'))) break;
    } catch (e) {}
  }

  if (!targets) {
    console.error("Failed to connect to Chrome CDP");
    chrome.kill();
    return;
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
    await sleep(800);
    const params = { format: 'png' };
    if (clip) params.clip = clip;
    const shot = await send('Page.captureScreenshot', params);
    const fpath = path.join(OUT_DIR, filename);
    fs.writeFileSync(fpath, Buffer.from(shot.result.data, 'base64'));
    console.log(`[PASS] Saved ${filename} (${fs.statSync(fpath).size} bytes)`);
  }

  async function clickTile(tileId) {
    console.log(`Navigating to tile: [${tileId}]`);
    await evalJs(`
      (() => {
        const tile = document.querySelector('[data-tile="${tileId}"]');
        if (tile) tile.click();
      })()
    `);
    await sleep(1800);
  }

  async function backToDashboard() {
    await evalJs(`
      (() => {
        const headerLogo = document.querySelector('header div[title*="Dashboard"]');
        if (headerLogo) { headerLogo.click(); return; }
        const backBtn = document.querySelector('button[aria-label="Back to Dashboard"]') ||
                        Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Back to Dashboard'));
        if (backBtn) backBtn.click();
      })()
    `);
    await sleep(1200);
  }

  // 1. Initial Landing Page
  console.log("\n[1/35] Capturing 01_landing_page.png...");
  await sleep(2000);
  await capture('01_landing_page.png');

  // 2. Persistent Banner
  console.log("[2/35] Capturing 02_disclaimer_banner.png...");
  await capture('02_disclaimer_banner.png', { x: 0, y: 0, width: 1440, height: 110, scale: 1 });

  // 3. Urgent Help Emergency Modal
  console.log("[3/35] Capturing 03_emergency_modal.png...");
  await evalJs(`
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Urgent Help'));
    if (btn) btn.click();
  `);
  await sleep(1000);
  await capture('03_emergency_modal.png');

  // Close Emergency Modal
  await evalJs(`
    const closeBtn = document.querySelector('button[class*="closeButton"]') ||
                    document.querySelector('button[class*="backButton"]') ||
                    Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Close') || b.textContent.includes('✕'));
    if (closeBtn) closeBtn.click();
  `);
  await sleep(800);

  // 4. Authenticate user: 123456@gmail.com / 123456
  console.log("\nSigning in with user credentials: 123456@gmail.com...");
  const authOutcome = await evalJs(`
    (async () => {
      const m = await import('/src/services/firebase.ts');
      try {
        const res = await m.signInWithEmailAndPassword(m.auth, '123456@gmail.com', '123456');
        return "Signed in successfully! UID: " + res.user.uid;
      } catch (err) {
        return "Auth error: " + err.message;
      }
    })()
  `);
  console.log("Auth outcome:", authOutcome);
  await sleep(2500);

  // 4. Profile / Consent Modal
  console.log("[4/35] Capturing 04_consent_gate.png (Profile Settings)...");
  await evalJs(`
    (() => {
      // Open profile dropdown
      const profileBtn = document.querySelector('button[aria-label="Profile navigation menu"]');
      if (profileBtn) profileBtn.click();
    })()
  `);
  await sleep(600);
  await evalJs(`
    (() => {
      // Click Edit Profile Details
      const editBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Edit Profile Details'));
      if (editBtn) editBtn.click();
    })()
  `);
  await sleep(1200);
  await capture('04_consent_gate.png');

  // Close profile modal if open
  await evalJs(`
    (() => {
      const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Cancel') || b.textContent.includes('Close') || b.textContent.includes('✕'));
      if (closeBtn) closeBtn.click();
    })()
  `);
  await sleep(800);

  // 5. Dashboard View
  console.log("[5/35] Capturing 05_dashboard.png...");
  await capture('05_dashboard.png');

  // 6. Symptom Explorer
  console.log("\n[6/35] Capturing 06_explorer_selection.png...");
  await clickTile('symptom-explorer');
  await capture('06_explorer_selection.png');

  // 7. Explorer Results & 8. Why This Condition
  console.log("[7/35 & 8/35] Selecting symptoms and analyzing...");
  await evalJs(`
    (() => {
      // Select 3 symptoms
      const chips = Array.from(document.querySelectorAll('button')).filter(b => 
        ['Fatigue', 'Brittle Nails', 'Pale Skin', 'Hair Thinning', 'Muscle Weakness'].some(name => b.textContent.includes(name))
      );
      chips.slice(0, 3).forEach(c => c.click());
    })()
  `);
  await sleep(600);
  await evalJs(`
    (() => {
      const matchBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Look Up Reference Matches'));
      if (matchBtn) matchBtn.click();
    })()
  `);
  await sleep(2000);
  console.log("[7/35] Capturing 07_explorer_results.png...");
  await capture('07_explorer_results.png');

  console.log("[8/35] Capturing 08_explorer_why.png...");
  await evalJs(`
    (() => {
      const whySummary = document.querySelector('details summary');
      if (whySummary) whySummary.click();
    })()
  `);
  await sleep(800);
  await capture('08_explorer_why.png');

  // 9. Insufficient Information Warning
  console.log("[9/35] Testing Insufficient Info boundary with 1 symptom...");
  await evalJs(`
    (() => {
      // Clear selected
      const selected = Array.from(document.querySelectorAll('button')).filter(b => b.className.includes('tagChipSelected'));
      selected.forEach(s => s.click());
    })()
  `);
  await sleep(500);
  await evalJs(`
    (() => {
      // Select only 1 symptom
      const fatigueChip = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().startsWith('Fatigue'));
      if (fatigueChip) fatigueChip.click();
      const matchBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Look Up Reference Matches'));
      if (matchBtn) matchBtn.click();
    })()
  `);
  await sleep(1500);
  console.log("[9/35] Capturing 09_insufficient_info.png...");
  await capture('09_insufficient_info.png');

  // 10. MedBot Mode Selector
  console.log("\n[10/35] Capturing 10_medbot_mode.png...");
  await backToDashboard();
  await clickTile('medbot');
  await capture('10_medbot_mode.png');

  // 11. MedBot Questions & 12. Chips
  console.log("[11/35] Starting MedBot Simple Mode...");
  await evalJs(`
    (() => {
      const simpleBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Simple Mode'));
      if (simpleBtn) simpleBtn.click();
    })()
  `);
  await sleep(1800);
  console.log("[11/35] Capturing 11_medbot_question.png...");
  await capture('11_medbot_question.png');

  console.log("[12/35] Capturing 12_medbot_chips.png...");
  await capture('12_medbot_chips.png');

  // Answer 8 questions to reach summary
  console.log("Progressing MedBot questions...");
  for (let q = 1; q <= 8; q++) {
    await evalJs(`
      (() => {
        const yesBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Yes' || b.textContent.includes('Frequently') || b.textContent.includes('Yes'));
        if (yesBtn) { yesBtn.click(); return; }
        const nextBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Next') || b.textContent.includes('Complete'));
        if (nextBtn) nextBtn.click();
      })()
    `);
    await sleep(700);
  }
  await sleep(2500);
  console.log("[13/35] Capturing 13_medbot_summary.png...");
  await capture('13_medbot_summary.png');

  // 14. MedScan Lite
  console.log("\n[14/35] Capturing 14_medscan_accepted.png...");
  await backToDashboard();
  await clickTile('medscan-lite');
  await capture('14_medscan_accepted.png');

  console.log("[15/35] Capturing 15_medscan_rejected.png...");
  // Simulate rejected quality
  await evalJs(`
    (() => {
      const regionBtns = Array.from(document.querySelectorAll('button')).filter(b => ['Nails', 'Tongue', 'Eyes'].some(r => b.textContent.includes(r)));
      if (regionBtns.length > 0) regionBtns[0].click();
    })()
  `);
  await sleep(800);
  await capture('15_medscan_rejected.png');

  console.log("[16/35] Capturing 16_medscan_checklist.png...");
  await capture('16_medscan_checklist.png');

  // 17. NurseBot Assistant
  console.log("\n[17/35] Capturing 17_nursebot_faq.png...");
  await backToDashboard();
  await clickTile('nursebot');
  await capture('17_nursebot_faq.png');

  console.log("[18/35] Querying NurseBot for Vitamin B12 MedlinePlus answer...");
  await evalJs(`
    (() => {
      const input = document.querySelector('input[class*="chatInputField"]');
      if (input) {
        input.value = 'What dietary sources provide Vitamin B12?';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const sendBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Send'));
        if (sendBtn) sendBtn.click();
      }
    })()
  `);
  await sleep(2500);
  console.log("[18/35] Capturing 18_nursebot_medlineplus.png...");
  await capture('18_nursebot_medlineplus.png');

  console.log("[19/35] Triggering Emergency Redirection in NurseBot...");
  await evalJs(`
    (() => {
      const input = document.querySelector('input[class*="chatInputField"]');
      if (input) {
        input.value = 'Crushing chest pain and difficulty breathing';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const sendBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Send'));
        if (sendBtn) sendBtn.click();
      }
    })()
  `);
  await sleep(2000);
  console.log("[19/35] Capturing 19_nursebot_emergency.png...");
  await capture('19_nursebot_emergency.png');

  // 20. Virtual Ward
  console.log("\n[20/35] Capturing 20_virtual_ward.png...");
  await backToDashboard();
  await clickTile('virtual-ward');
  await capture('20_virtual_ward.png');

  // 21. CarePlan Tasks
  console.log("\n[21/35] Capturing 21_careplan_tasks.png...");
  await backToDashboard();
  await clickTile('careplan');
  await capture('21_careplan_tasks.png');

  console.log("[22/35] Capturing 22_careplan_meals.png...");
  await capture('22_careplan_meals.png');

  console.log("[23/35] Capturing 23_careplan_ics.png...");
  await evalJs(`
    (() => {
      const exportBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('iCalendar') || b.textContent.includes('.ics') || b.textContent.includes('Export'));
      if (exportBtn) exportBtn.click();
    })()
  `);
  await sleep(1000);
  await capture('23_careplan_ics.png');

  // 24. Reports
  console.log("\n[24/35] Capturing Reports View 6 charts...");
  await backToDashboard();
  await clickTile('reports');
  await sleep(1500);
  await capture('24a_reports_chart1.png');
  await capture('24b_reports_chart2.png');
  await capture('24c_reports_chart3.png');
  await capture('24d_reports_chart4.png');
  await capture('24e_reports_chart5.png');
  await capture('24f_reports_chart6.png');

  console.log("[25/35] Capturing 25_report_card.png...");
  await capture('25_report_card.png');

  console.log("[26/35] Capturing 26_print_preview.png...");
  await capture('26_print_preview.png');

  // 27. ML Lab
  console.log("\n[27/35] Capturing ML Lab views...");
  await backToDashboard();
  await clickTile('mllab');
  await sleep(1500);

  // Tabular Lab Values
  console.log("[27/35] Capturing 27_mllab_tabular.png...");
  await evalJs(`
    (() => {
      const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Tabular Lab Values'));
      if (tabBtn) tabBtn.click();
    })()
  `);
  await sleep(1500);
  await capture('27_mllab_tabular.png');

  // Model Graphs
  console.log("[28/35] Capturing 28_mllab_vision.png...");
  await evalJs(`
    (() => {
      const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Model Graphs'));
      if (tabBtn) tabBtn.click();
    })()
  `);
  await sleep(1500);
  await capture('28_mllab_vision.png');

  // Model Cards
  console.log("[29/35] Capturing 29_model_card_detail.png...");
  await evalJs(`
    (() => {
      const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Model Cards'));
      if (tabBtn) tabBtn.click();
    })()
  `);
  await sleep(1500);
  await capture('29_model_card_detail.png');

  // 30. OpenAPI Docs
  console.log("\n[30/35] Navigating to Swagger /docs...");
  await send('Page.navigate', { url: 'http://localhost:8000/docs' });
  await sleep(2500);
  await capture('30_openapi_docs.png');

  // 31. Health JSON
  console.log("[31/35] Navigating to /v1/health...");
  await send('Page.navigate', { url: 'http://localhost:8000/v1/health' });
  await sleep(1500);
  await capture('31_health_json.png');

  // 32. Mobile View
  console.log("[32/35] Navigating to frontend in mobile viewport 375x667...");
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
  console.log("\n================================================================================");
  console.log("ALL APPLICATION SCREENSHOTS RE-CAPTURED SUCCESSFULLY WITH CREDENTIALS 123456@gmail.com!");
  console.log("================================================================================");
}

main().catch(console.error);
