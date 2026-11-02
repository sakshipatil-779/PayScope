const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ARTIFACTS_BRAIN_DIR = path.resolve("C:/Users/patil/.gemini/antigravity/brain/d4d8734d-238f-42fa-a6a6-41096130c7d7");
const SCREENSHOT_DIR = path.resolve(__dirname, "../artifacts/screenshots");

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function saveDual(filename, buffer) {
  fs.writeFileSync(path.join(SCREENSHOT_DIR, filename), buffer);
  try {
    fs.writeFileSync(path.join(ARTIFACTS_BRAIN_DIR, filename), buffer);
  } catch (e) {
    // ignore
  }
  console.log(`Saved artifact: ${filename}`);
}

async function run() {
  console.log("=== STARTING PAYSCOPE VALIDATION SUITE ===");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  // Step 1: Clean session landing visit
  console.log("1. Visiting landing page with clean session...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  // Capture 01_landing_visible_video_loop.png
  const sc1 = await page.screenshot();
  saveDual("01_landing_visible_video_loop.png", sc1);

  // Step 2: Exact picker card-selection moment
  console.log("2. Navigating to picker card-selection moment (t = 4.18s)...");
  await page.evaluate(async () => {
    const v = document.getElementById("intro-video");
    if (v) {
      v.pause();
      v.currentTime = 4.18;
      await new Promise((r) => {
        if (v.seeking) v.onseeked = r;
        else r();
      });
    }
  });
  await page.waitForTimeout(300);

  const sc2 = await page.screenshot();
  saveDual("02_picker_card_selection_moment.png", sc2);

  // Step 3: Complete transition to website reveal
  console.log("3. Completing intro transition...");
  await page.evaluate(() => {
    const v = document.getElementById("intro-video");
    if (v) {
      v.play().catch(() => {});
    }
  });
  // Wait for 3D emergence and flight to complete
  await page.waitForTimeout(1400);

  // Check hamburger and logo positioning at extreme top-left
  const navLayout = await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="Open navigation menu"]');
    const logo = document.getElementById("header-target-logo");
    const header = document.querySelector("header > div");
    return {
      hamburgerRect: btn ? btn.getBoundingClientRect() : null,
      logoRect: logo ? logo.getBoundingClientRect() : null,
      headerPaddingLeft: header ? window.getComputedStyle(header).paddingLeft : null,
    };
  });
  console.log("Extreme Top-Left Navigation Layout:", navLayout);

  const sc3 = await page.screenshot();
  saveDual("03_top_left_hamburger_and_logo.png", sc3);

  // Step 4: Final landing page with ambient video looping behind hero
  console.log("4. Capturing final landing page with ambient background video...");
  await page.waitForTimeout(600);
  const sc4 = await page.screenshot();
  saveDual("04_final_landing_page.png", sc4);

  // Step 5: Dashboard with live data
  console.log("5. Navigating to /dashboard...");
  await page.goto("http://localhost:3000/dashboard", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);

  // Check metrics rendered on dashboard
  const dashboardStats = await page.evaluate(() => {
    const text = document.body.innerText;
    return {
      hasActiveCommitments: text.includes("Active Commitments"),
      hasMonthlySpend: text.includes("Monthly Spend"),
      hasInsights: text.includes("Open Insights"),
      hasSuraksha: text.includes("Suraksha General Insurance") || text.includes("DevStack"),
      hasUnavailable: text.includes("Dashboard Service Unavailable"),
    };
  });
  console.log("Dashboard Live Stats Check:", dashboardStats);

  const sc5 = await page.screenshot();
  saveDual("05_dashboard_live_data.png", sc5);

  // Step 6: Empty or Degraded Dashboard Handling
  console.log("6. Testing degraded / offline simulation...");
  const degradedContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const degradedPage = await degradedContext.newPage();
  // Route /api/v1/dashboard/summary to simulate offline state
  await degradedPage.route("**/api/v1/dashboard/summary", (route) => {
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Service Temporarily Unavailable" }),
    });
  });
  await degradedPage.goto("http://localhost:3000/dashboard", { waitUntil: "domcontentloaded" });
  await degradedPage.waitForTimeout(800);

  const sc6 = await degradedPage.screenshot();
  saveDual("06_dashboard_empty_or_degraded.png", sc6);
  await degradedContext.close();

  // Step 7: Mobile landing page (390x844)
  console.log("7. Mobile Landing Page...");
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    storageState: undefined,
  });
  const mobilePage = await mobileContext.newPage();
  // Set session seen so mobile views the revealed landing page directly
  await mobilePage.addInitScript(() => {
    sessionStorage.setItem("payscope_intro_transition_seen", "true");
  });
  await mobilePage.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await mobilePage.waitForTimeout(800);

  const sc7 = await mobilePage.screenshot();
  saveDual("07_mobile_landing_page.png", sc7);

  // Step 8: Mobile dashboard
  console.log("8. Mobile Dashboard...");
  await mobilePage.goto("http://localhost:3000/dashboard", { waitUntil: "domcontentloaded" });
  await mobilePage.waitForTimeout(1200);

  const sc8 = await mobilePage.screenshot();
  saveDual("08_mobile_dashboard.png", sc8);
  await mobileContext.close();

  await browser.close();
  console.log("=== ALL 8 ARTIFACT SCREENSHOTS GENERATED SUCCESSFULLY ===");
}

run().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
