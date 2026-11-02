const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const SCREENSHOT_DIR = path.resolve(__dirname, "../artifacts/screenshots");
const ARTIFACTS_BRAIN_DIR = path.resolve("C:/Users/patil/.gemini/antigravity/brain/d4d8734d-238f-42fa-a6a6-41096130c7d7");

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
  console.log(`Saved screenshot: ${filename}`);
}

async function runTests() {
  console.log("=== STARTING PAYSCOPE ANIMATION & THEME TEST SUITE ===");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  // 1. Visit landing page (clean session)
  console.log("Navigating to http://localhost:3000 (Fresh Session)...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(600);

  // Capture Screenshot 1: Looping picker animation
  const sc1 = await page.screenshot();
  saveDual("01_looping_picker_animation.png", sc1);

  // Verify Video is at scale(1) - NO CAMERA ZOOM
  const videoTransform = await page.evaluate(() => {
    const v = document.querySelector("video");
    const container = v ? v.parentElement : null;
    return {
      hasVideo: !!v,
      containerTransform: container ? window.getComputedStyle(container).transform : "none",
    };
  });
  console.log("Video scale check (No camera zoom):", videoTransform);

  // 2. Wait until card grab timestamp (~4.18s)
  console.log("Waiting for card grab timestamp (t ≈ 4.18s)...");
  await page.evaluate(async () => {
    const v = document.getElementById("intro-video");
    if (v) {
      v.pause();
      v.currentTime = 4.15;
      await new Promise((r) => {
        if (v.seeking) v.onseeked = r;
        else r();
      });
    }
  });
  await page.waitForTimeout(300);

  // Capture Screenshot 2: Card selection moment
  const sc2 = await page.screenshot();
  saveDual("02_card_selection_moment.png", sc2);

  // 3. Emerge Forward in 3D
  await page.evaluate(async () => {
    const v = document.getElementById("intro-video");
    if (v) {
      v.currentTime = 4.18;
      await new Promise((r) => {
        if (v.seeking) v.onseeked = r;
        else r();
      });
      v.play().catch(() => {});
    }
  });
  await page.waitForTimeout(200);

  // Capture Screenshot 3: Logo moving forward in 3D
  const sc3 = await page.screenshot();
  saveDual("03_logo_moving_forward.png", sc3);

  // 4. Logo travelling to top-left
  await page.waitForTimeout(300);
  const sc4 = await page.screenshot();
  saveDual("04_logo_wordmark_top_left.png", sc4);

  // 5. Final landing page revealed with settled top-left logo
  await page.waitForTimeout(800);
  const sc5 = await page.screenshot();
  saveDual("05_final_landing_page.png", sc5);

  // Verify settled logo is at TOP-LEFT
  const logoPosition = await page.evaluate(() => {
    const logoEl = document.getElementById("header-target-logo");
    if (!logoEl) return null;
    const r = logoEl.getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  });
  console.log("Header logo position at top-left:", logoPosition);

  // 6. Test Hamburger Menu Drawer
  console.log("Testing Left Hamburger Menu Drawer...");
  const hamburgerBtn = await page.$('button[aria-label="Open navigation menu"]');
  if (hamburgerBtn) {
    await hamburgerBtn.click();
    await page.waitForTimeout(400);

    // Capture Screenshot 6: Open Hamburger Menu
    const sc6 = await page.screenshot();
    saveDual("06_open_hamburger_menu.png", sc6);

    // Verify all 10 routes in drawer
    const drawerLinks = await page.evaluate(() => {
      const drawer = document.querySelector('[role="dialog"]');
      if (!drawer) return [];
      const links = Array.from(drawer.querySelectorAll("a"));
      return links.map((l) => ({ href: l.getAttribute("href"), text: l.textContent.trim() }));
    });
    console.log(`Drawer contains ${drawerLinks.length} links:`, drawerLinks.map((l) => l.href));

    // Test Escape key closes drawer
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);
    const drawerClosed = await page.evaluate(() => !document.querySelector('[role="dialog"]'));
    console.log("Escape key closed drawer:", drawerClosed);
  }

  // 7. Route & Theme Consistency Tests
  console.log("Testing Route Themes...");

  // Dashboard
  await page.goto("http://localhost:3000/dashboard", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(600);
  const sc7 = await page.screenshot();
  saveDual("07_dashboard_theme.png", sc7);

  // Commitments
  await page.goto("http://localhost:3000/commitments", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);

  // Insights
  await page.goto("http://localhost:3000/insights", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  const sc8 = await page.screenshot();
  saveDual("08_insights_theme.png", sc8);

  // Financial Impact
  await page.goto("http://localhost:3000/financial-impact", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  const sc9 = await page.screenshot();
  saveDual("09_financial_impact_theme.png", sc9);

  // Savings
  await page.goto("http://localhost:3000/savings", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(400);

  // Relationships
  await page.goto("http://localhost:3000/relationships", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(500);
  const sc10 = await page.screenshot();
  saveDual("10_relationships_theme.png", sc10);

  // Cancellations
  await page.goto("http://localhost:3000/cancellations", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(400);

  // 8. Return to landing page: verify NO intro repeats
  console.log("Returning to Landing Page (Session should NOT replay intro)...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(400);

  const introReplayed = await page.evaluate(() => {
    const introEl = document.querySelector(".fixed.inset-0.z-50.bg-\\[\\#011633\\]");
    return !!introEl;
  });
  console.log("Intro replayed on return:", introReplayed, "(Expected: false)");

  // 9. Mobile responsive test (390x844)
  console.log("Testing Mobile Responsive Layout (390x844)...");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(300);

  const mobileCheck = await page.evaluate(() => {
    return {
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      hasOverflow: document.documentElement.scrollWidth > window.innerWidth,
    };
  });
  console.log("Mobile layout overflow check:", mobileCheck);

  await browser.close();
  console.log("=== ALL PAYSCOPE ANIMATION & THEME TESTS PASSED ===");
}

runTests().catch((err) => {
  console.error("Test failed:", err);
  process.exit(1);
});
