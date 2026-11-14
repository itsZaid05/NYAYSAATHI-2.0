// Run against a local integrated server: NYAY_TEST_URL=http://127.0.0.1:8010 node tests/browser.cjs
// Uses the environment's Playwright and system Chromium; no external assets are required.
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const base = process.env.NYAY_TEST_URL || "http://127.0.0.1:8010";
(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
    headless: true,
    args: ["--no-sandbox"],
  });
  const context = await browser.newContext({
    acceptDownloads: true,
    viewport: { width: 1440, height: 1050 },
  });
  const page = await context.newPage();
  let errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(base);
  await page
    .getByRole("button", { name: "Fill laptop demonstration", exact: true })
    .click();
  await page.getByRole("checkbox").nth(0).check();
  await page.getByRole("checkbox").nth(1).check();
  await page
    .getByRole("button", { name: "Create confidential case", exact: true })
    .click();
  await page.getByRole("heading", { name: "We’re listening" }).waitFor();
  await page
    .locator("#message-form textarea")
    .fill("I asked Demo Seller on 2026-10-04. The platform was Demo Shop.");
  await page
    .getByRole("button", { name: "Save follow-up", exact: true })
    .click();
  await page
    .getByText("The platform was Demo Shop.", { exact: false })
    .first()
    .waitFor();
  await page.getByRole("button", { name: "Add evidence", exact: true }).click();
  for (const kind of ["invoice", "fault", "communication", "warranty"]) {
    await page.locator('select[name="kind"]').selectOption(kind);
    await page
      .locator('input[type="file"]')
      .setInputFiles({
        name: `${kind}.txt`,
        mimeType: "text/plain",
        buffer: Buffer.from(
          `Fictional ${kind}. Demo Seller, 2026-10-01. Laptop purchase.`,
        ),
      });
    const response = page.waitForResponse(
      (r) => r.url().endsWith("/evidence") && r.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Upload and extract", exact: true })
      .click();
    assert.equal((await response).status(), 200);
    await page
      .getByRole("heading", { name: `${kind}.txt`, exact: true })
      .waitFor();
  }
  await page.locator('[data-page="case-summary"]').click();
  assert.match(await page.locator("#view").innerText(), /Strong/);
  await page
    .getByRole("button", { name: "Prepare seller letter", exact: true })
    .click();
  await page.locator("#draft-form textarea").waitFor();
  await page
    .locator("#draft-form textarea")
    .fill(
      "Fictional edited request to Demo Seller. Please review my defective laptop.",
    );
  const save = page.waitForResponse(
    (r) => r.url().endsWith("/draft") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Save edits", exact: true }).click();
  assert.equal((await save).status(), 200);
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download case packet PDF", exact: true })
    .click();
  const file = await download;
  assert.equal(file.suggestedFilename(), "nyaysaathi-case-packet.pdf");
  assert.equal(await file.failure(), null);
  await page.reload();
  await page.locator("#draft-form textarea").waitFor();
  assert.match(
    await page.locator("#draft-form textarea").inputValue(),
    /Fictional edited request/,
  );
  await page.locator('[data-page="story-mode"]').click();
  assert.match(await page.locator("#view").innerText(), /not a judgment/);
  await page.locator('[data-page="ai-insights"]').click();
  assert.match(
    await page.locator("#view").innerText(),
    /No reviewed legal passages/,
  );
  await page.locator('[data-page="marketplace"]').click();
  assert.match(
    await page.locator("#view").innerText(),
    /not a verified advocate/,
  );
  if (
    (await page
      .getByRole("button", { name: "Share reviewed packet" })
      .isEnabled()) === false
  )
    assert.match(await page.locator("#view").innerText(), /Handoff disabled/);
  else {
    await page.locator('#share-form input[type="checkbox"]').check();
    const share = page.waitForResponse((r) => r.url().endsWith("/share"));
    await page
      .getByRole("button", { name: "Share reviewed packet", exact: true })
      .click();
    assert.equal((await share).status(), 200);
    await page
      .getByText("Current handoff: shared_with_demo_lawyer", { exact: false })
      .waitFor();
    const lc = await browser.newContext({ acceptDownloads: true });
    const lp = await lc.newPage();
    lp.on("pageerror", (e) => errors.push(e.message));
    await lp.goto(base);
    await lp.locator('[data-page="marketplace"]').click();
    await lp.locator("#lawyer-form input").fill(
      require("node:fs")
        .readFileSync(
          process.env.NYAY_LAWYER_PASSWORD_FILE ||
            "runtime/demo-lawyer-password",
          "utf8",
        )
        .trim(),
    );
    await lp
      .getByRole("button", { name: "Open demo inbox", exact: true })
      .click();
    await lp
      .getByRole("button", { name: "Acknowledge demo receipt", exact: true })
      .waitFor();
    const sharedDownload = lp.waitForEvent("download");
    await lp
      .getByRole("link", { name: "Download shared snapshot", exact: true })
      .click();
    assert.equal(await (await sharedDownload).failure(), null);
    await lp
      .getByRole("button", { name: "Acknowledge demo receipt", exact: true })
      .click();
    await lp
      .getByText("Demo acknowledgment recorded", { exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "Revoke inbox access", exact: true })
      .click();
    await page
      .getByRole("heading", { name: "Your account of events", exact: true })
      .waitFor();
    await lp.reload();
    await lp.locator('[data-page="marketplace"]').click();
    await lp
      .getByText("No voluntarily shared packets.", { exact: true })
      .waitFor();
    await lc.close();
    console.log(
      "PASS: browser explicit share, separate authenticated demo lawyer inbox, shared PDF download, acknowledgment and revocation.",
    );
  }
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.locator('[data-page="help"]').click();
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
      `horizontal overflow at ${width}`,
    );
  }
  await page
    .getByRole("button", { name: "हिंदी में बदलें", exact: true })
    .click();
  assert.equal(await page.locator("html").getAttribute("lang"), "hi");
  assert.match(await page.locator("#view").innerText(), /आधिकारिक/);
  await page.screenshot({ path: "runtime/mobile-hi.png", fullPage: true });
  await page
    .getByRole("button", { name: "Switch to English", exact: true })
    .click();
  await page.locator('[data-page="settings"]').click();
  page.once("dialog", (d) => d.accept());
  await page
    .getByRole("button", {
      name: "Delete this case and its files",
      exact: true,
    })
    .click();
  await page.getByRole("heading", { name: "Your saved cases" }).waitFor();
  assert.match(
    await page.locator("#view").innerText(),
    /No cases in this session/,
  );
  assert.deepEqual(errors, []);
  console.log(
    "PASS: browser intake, follow-up, 4 evidence uploads, readiness, draft edit, PDF download, reload persistence, story, abstention, demo handoff boundary, 3 viewports, Hindi and deletion; no page errors.",
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
