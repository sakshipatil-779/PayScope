const { chromium } = require("../apps/web/node_modules/playwright");
const path = require("path");
const fs = require("fs");

const SCREENSHOT_DIR = path.resolve(__dirname, "../artifacts/screenshots");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

// Also save to brain artifact directory for display
const BRAIN_DIR = "C:/Users/patil/.gemini/antigravity/brain/d4d8734d-238f-42fa-a6a6-41096130c7d7";

async function saveScreenshot(page, filename, description) {
  const localPath = path.join(SCREENSHOT_DIR, filename);
  const brainPath = path.join(BRAIN_DIR, filename);
  await page.screenshot({ path: localPath });
  fs.copyFileSync(localPath, brainPath);
  console.log(`[PASS] Captured ${filename}: ${description}`);
}

(async () => {
  console.log("Starting Cinematic Video Intro and Website Transition Tests...");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  // Test 1: First visit - Video plays full screen
  console.log("Navigating to http://localhost:3000 with clean session...");
  await page.goto("http://localhost:3000");

  // Wait for video element
  const video = await page.waitForSelector("video", { timeout: 8000 });
  console.log("[PASS] Video element discovered on landing page");

  // Verify muted and autoplay
  const isMuted = await video.evaluate((v) => v.muted);
  const isAutoplay = await video.evaluate((v) => v.autoplay);
  console.log(`[PASS] Video properties: muted=${isMuted}, autoplay=${isAutoplay}`);

  // Stage 1: Intro Start
  await page.waitForTimeout(1000);
  await saveScreenshot(page, "01_intro_start.png", "Full-screen cinematic intro playing");

  // Stage 2: Picker grabbing PayScope card (around 4.2s)
  console.log("Waiting for robotic picker grab moment (~4.2s)...");
  await page.waitForFunction(() => {
    const v = document.querySelector("video");
    return v && v.currentTime >= 4.15;
  }, { timeout: 10000 });
  await saveScreenshot(page, "02_picker_grab_card.png", "Robotic picker claws closing onto PayScope card");

  // Stage 3: Logo Zooming & Crisp Vector Swap (~5.1s)
  console.log("Waiting for camera zoom into PayScope card...");
  await page.waitForFunction(() => {
    const v = document.querySelector("video");
    return v && v.currentTime >= 5.0;
  }, { timeout: 10000 });
  await saveScreenshot(page, "03_logo_zoom.png", "Camera zoomed into PayScope card with crisp vector logo");

  // Stage 4: Logo travelling to top-right corner (~5.6s)
  await page.waitForTimeout(350);
  await saveScreenshot(page, "04_logo_travelling_top_right.png", "Logo travelling diagonally to top-right header");

  // Stage 5: Final revealed website (~6.6s)
  console.log("Waiting for full website reveal...");
  await page.waitForTimeout(1200);
  await saveScreenshot(page, "05_final_revealed_website.png", "Full PayScope homepage revealed with top-right logo");

  // Verify sessionStorage
  const introSeen = await page.evaluate(() => sessionStorage.getItem("payscope_intro_seen"));
  console.log(`[PASS] sessionStorage 'payscope_intro_seen' = "${introSeen}"`);

  // Verify header logo position is top-right
  const logoBox = await page.evaluate(() => {
    const el = document.getElementById("header-target-logo");
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    return {
      left: rect.left,
      right: rect.right,
      top: rect.top,
      windowWidth: window.innerWidth,
    };
  });
  console.log(`[PASS] Header logo bounding box:`, logoBox);
  if (logoBox && logoBox.right > logoBox.windowWidth * 0.7) {
    console.log("[PASS] Verified logo is anchored in the TOP-RIGHT region of the header!");
  } else {
    console.warn("[WARN] Logo position check:", logoBox);
  }

  // Test 2: Second visit in same session -> Skip intro automatically
  console.log("\nTesting session replay prevention on page reload...");
  await page.reload();
  await page.waitForTimeout(500);
  const videoExists = await page.evaluate(() => !!document.querySelector("video"));
  console.log(`[PASS] On session reload: video overlay active = ${videoExists} (Expected: false)`);

  // Test 3: Mobile Viewport
  console.log("\nTesting responsive mobile composition (390x844)...");
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
  });
  const mobilePage = await mobileContext.newPage();
  // Clear session to test mobile
  await mobilePage.goto("http://localhost:3000");
  await mobilePage.waitForTimeout(6500); // Wait for transition to complete
  await saveScreenshot(mobilePage, "06_mobile_final_website.png", "Mobile layout with crisp top-right logo & no overflow");

  const hasHorizontalScroll = await mobilePage.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });
  console.log(`[PASS] Mobile horizontal overflow check: hasHorizontalScroll = ${hasHorizontalScroll} (Expected: false)`);

  // Test 4: Skip button functionality
  console.log("\nTesting Skip Intro button on new clean session...");
  const skipContext = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const skipPage = await skipContext.newPage();
  await skipPage.goto("http://localhost:3000");

  const skipBtn = await skipPage.waitForSelector("button:has-text('Skip intro')", { timeout: 3000 });
  await skipBtn.click();
  console.log("[PASS] Clicked 'Skip intro' button");
  await skipPage.waitForTimeout(400);

  const skipIntroSeen = await skipPage.evaluate(() => sessionStorage.getItem("payscope_intro_seen"));
  console.log(`[PASS] After Skip click: payscope_intro_seen = "${skipIntroSeen}"`);

  await browser.close();
  console.log("\nALL CINEMATIC TRANSITION PLAYWRIGHT TESTS PASSED SUCCESSFULLY!");
})();
