import assert from "node:assert/strict";
import fs from "node:fs";
import { chromium } from "playwright";

const baseUrl = (process.env.BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const expectedCommit = (process.env.EXPECTED_COMMIT || "").trim();
const timeoutMs = Number(process.env.BROWSER_SMOKE_TIMEOUT_MS || "180000");
const artifactsDir = "artifacts";
fs.mkdirSync(artifactsDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const pageErrors = [];
const summary = {};

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  page.on("pageerror", error => pageErrors.push(String(error)));

  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  assert.match(await page.title(), /PlanProbe/);

  const release = await page.evaluate(async () => {
    const response = await fetch("/api/release");
    if (!response.ok) throw new Error(`release HTTP ${response.status}`);
    return await response.json();
  });
  if (expectedCommit) assert.equal(release.commit, expectedCommit, "browser hit a stale Render commit");

  await page.waitForFunction(
    () => document.querySelector("#status-line")?.textContent?.includes("준비 완료"),
    null,
    { timeout: 30000 },
  );
  assert.equal(await page.locator("#run-demo").isEnabled(), true);
  await page.screenshot({ path: `${artifactsDir}/live-desktop-before.png`, fullPage: true });

  await page.locator("#run-demo").click();
  await page.waitForFunction(
    () => document.querySelector("#stage-pill")?.textContent === "검증 완료",
    null,
    { timeout: timeoutMs },
  );

  const result = await page.evaluate(() => ({
    stage: document.querySelector("#stage-pill")?.textContent?.trim() || "",
    headline: document.querySelector("#result-headline")?.textContent?.trim() || "",
    falsePremises: document.querySelector("#metric-false")?.textContent?.trim() || "",
    preEdits: document.querySelector("#metric-preedit")?.textContent?.trim() || "",
    checks: document.querySelector("#metric-checks")?.textContent?.trim() || "",
    gate: document.querySelector("#gate-banner")?.textContent?.trim() || "",
    diff: document.querySelector("#diff")?.textContent?.trim() || "",
    finalChecks: document.querySelector("#checks")?.textContent?.trim() || "",
  }));

  assert.equal(result.stage, "검증 완료");
  assert.equal(result.falsePremises, "2");
  assert.equal(result.preEdits, "0");
  assert.match(result.headline, /잘못된 전제 2개/);
  assert.match(result.gate, /코드 생성 차단/);
  assert.ok(result.diff.length > 0, "rendered patch section is empty");
  assert.ok(result.finalChecks.length > 0, "rendered final checks section is empty");
  assert.equal(pageErrors.length, 0, `browser page errors: ${pageErrors.join(" | ")}`);

  await page.screenshot({ path: `${artifactsDir}/live-desktop-complete.png`, fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForFunction(
    () => document.querySelector("#status-line")?.textContent?.includes("준비 완료"),
    null,
    { timeout: 30000 },
  );
  const overflowPx = await page.evaluate(
    () => Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
  );
  assert.ok(overflowPx <= 1, `mobile horizontal overflow: ${overflowPx}px`);
  await page.screenshot({ path: `${artifactsDir}/live-mobile.png`, fullPage: true });

  Object.assign(summary, {
    base_url: baseUrl,
    release,
    result,
    mobile_overflow_px: overflowPx,
    page_errors: pageErrors,
    status: "passed",
  });
} catch (error) {
  Object.assign(summary, {
    base_url: baseUrl,
    expected_commit: expectedCommit,
    page_errors: pageErrors,
    status: "failed",
    error: error instanceof Error ? error.stack || error.message : String(error),
  });
  throw error;
} finally {
  fs.writeFileSync(
    `${artifactsDir}/live-browser-summary.json`,
    JSON.stringify(summary, null, 2) + "\n",
    "utf8",
  );
  await browser.close();
}
