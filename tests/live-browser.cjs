// Explicit live-provider smoke test: only fictional data, never a mock AI response.
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
    headless: true,
    args: ["--no-sandbox"],
  });
  const p = await b.newPage({ viewport: { width: 1440, height: 1050 } });
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto(process.env.NYAY_TEST_URL || "http://127.0.0.1:8011");
  await p
    .getByRole("button", { name: "Fill laptop demonstration", exact: true })
    .click();
  await p
    .locator("#narrative")
    .fill(
      "Fictional: I purchased a laptop online from Demo Seller for INR 45000. It stopped working shortly after delivery. The seller refused a replacement. I have an invoice and warranty details and want a replacement.",
    );
  await p.locator('[name="processing"]').check();
  await p.locator('[name="fictional"]').check();
  await p.locator('[name="ai"]').check();
  const intake = p.waitForResponse(
    (r) => r.url().endsWith("/intake") && r.request().method() === "POST",
    { timeout: 90000 },
  );
  await p
    .getByRole("button", { name: "Create confidential case", exact: true })
    .click();
  const a = await (await intake).json();
  assert.match(a.ai_status, /^Gemini live/);
  assert.equal(a.amounts[0].value.includes("45000"), true);
  assert.ok(a.assistant_message.length > 20);
  assert.ok(a.unknowns.length);
  await p.getByRole("heading", { name: "We’re listening" }).waitFor();
  await p
    .locator("#message-form textarea")
    .fill(
      "I purchased it on 2026-10-01; it was delivered on 2026-10-03 and stopped working on 2026-10-04. The platform was Demo Shop.",
    );
  const follow = p.waitForResponse(
    (r) => r.url().endsWith("/message") && r.request().method() === "POST",
    { timeout: 90000 },
  );
  await p.getByRole("button", { name: "Save follow-up", exact: true }).click();
  const updated = await (await follow).json();
  assert.match(updated.ai_status, /^Gemini live/);
  assert.ok(updated.timeline.length >= 3);
  assert.ok(updated.conversation.length >= 4);
  await p.locator('[data-page="dashboard"]').click();
  await p.getByRole("heading", { name: "Your situation, organised" }).waitFor();
  await p.screenshot({
    path: "runtime/live-intake-desktop.png",
    fullPage: true,
  });
  await p.locator('[data-page="generated-documents"]').click();
  await p.locator('select[name="kind"]').selectOption("lawyer_brief");
  const generated = p.waitForResponse((r) => r.url().endsWith("/draft"));
  await p
    .getByRole("button", { name: "Generate editable document", exact: true })
    .click();
  assert.equal((await generated).status(), 200);
  await p.locator("form[data-draft]").waitFor();
  // Delete only the synthetic case this script created; never other user cases.
  const deletion = await p.evaluate(async (id) => {
    const csrf = decodeURIComponent(
      document.cookie
        .split("; ")
        .find((c) => c.startsWith("nyay_csrf="))
        .split("=")[1],
    );
    return (
      await fetch("/api/cases/" + id, {
        method: "DELETE",
        headers: { "X-CSRF-Token": csrf },
      })
    ).status;
  }, a.case_id);
  assert.equal(deletion, 200);
  assert.deepEqual(errors, []);
  console.log(
    "PASS LIVE: frontend -> authenticated API -> real Gemini intake and follow-up -> canonical entities/timeline/history -> generated document -> deletion.",
  );
  if (!updated.sources.length)
    console.log(
      "BLOCKED: official-law grounded segment was not tested because the approved corpus is empty.",
    );
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
