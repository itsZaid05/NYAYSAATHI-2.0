// A genuinely new narrative, entered without the predefined example button. Live Gemini required.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { chromium } = require("playwright");
(async () => {
  const base = process.env.NYAY_TEST_URL || "http://127.0.0.1:8011";
  const requireGrounded = process.argv.includes("--require-grounded");
  const healthResponse = await fetch(base + "/api/health");
  assert.equal(healthResponse.status, 200);
  const health = await healthResponse.json();
  if (requireGrounded && !health.reviewed_sources) {
    console.error(
      "BLOCKED: authentic-source browser acceptance requires an approved official corpus; health reports zero passages. No legal analysis or source success is simulated.",
    );
    process.exitCode = 2;
    return;
  }
  const b = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
    headless: true,
    args: ["--no-sandbox"],
  });
  const guest = await b.newContext({
    acceptDownloads: true,
    viewport: { width: 1440, height: 1050 },
  });
  const p = await guest.newPage();
  let errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto(base);
  await p
    .getByRole("button", { name: "Start a fictional case", exact: true })
    .click();
  const retry = p.getByRole("button", {
    name: "Retry AI connection",
    exact: true,
  });
  if (await retry.count()) {
    const checked = p.waitForResponse(
      (r) => r.url().endsWith("/provider/recheck"),
      { timeout: 90000 },
    );
    await retry.click();
    const checkResponse = await checked;
    assert.equal(checkResponse.status(), 200);
    assert.equal(
      (await checkResponse.json()).live_ai_available,
      true,
      "Provider remained unavailable after explicit recheck",
    );
  }
  const narrative =
    "Fictional: Demo Alder advertised a household gardening membership that could end at any time without more debits. It confirmed my cancellation on 2026-10-18 but debited INR 1450 again on 2026-11-04. Support refused my written request to reverse that extra payment, saying cancellation only pauses deliveries, contrary to the saved advertisement. I have the offer, acknowledgment and bank record.";
  await p.locator("#narrative").fill(narrative);
  await p.locator('[name="processing"]').check();
  await p.locator('[name="fictional"]').check();
  await p.locator('[name="ai"]').check();
  const response = p.waitForResponse(
    (r) => r.url().endsWith("/intake") && r.request().method() === "POST",
    { timeout: 90000 },
  );
  await p
    .getByRole("button", { name: "Create confidential case", exact: true })
    .click();
  const a = await (await response).json();
  assert.equal(
    a.scope_status,
    "consumer",
    `Live intake did not complete: ${a.ai_status}; ${a.safety_flags.join("; ")}`,
  );
  assert.match(a.understanding_method, /Gemini multi-issue/);
  for (const category of [
    "subscription_billing",
    "refund_refusal",
    "misleading_advertising",
  ]) {
    assert.ok(
      a.issue_details.some((i) => i.category === category),
      `Missing supported facet: ${category}`,
    );
  }
  if (requireGrounded) {
    assert.ok(
      a.sources.length > 0 && a.legal_analysis?.claims.length > 0,
      "No source-grounded legal analysis was accepted",
    );
    const { createHash } = require("node:crypto");
    for (const source of a.sources) {
      assert.match(new URL(source.url).hostname, /\.(gov|nic)\.in$/);
      const artifact = fs.readFileSync(
        "knowledge/artifacts/" + source.artifact_sha256,
      );
      assert.equal(
        createHash("sha256").update(artifact).digest("hex"),
        source.artifact_sha256,
      );
    }
    for (const claim of a.legal_analysis.claims) {
      assert.equal(claim.support_status, "supported");
      claim.source_ids.forEach((id, index) => {
        const source = a.sources.find((s) => s.id === id);
        assert.ok(
          source && source.quote.includes(claim.supporting_quotes[index]),
        );
      });
      assert.ok(claim.fact_quotes.every((quote) => narrative.includes(quote)));
    }
    await p.locator('[data-page="ai-insights"]').click();
    for (const source of a.sources) {
      assert.ok(
        await p.locator(`a[href="${source.url}"]`).count(),
        "Official source link absent from frontend",
      );
    }
    console.log(
      "AUTHENTIC-SOURCE STRUCTURAL CHECKS PASSED; substantive legal accuracy still requires independent qualified review.",
    );
    await p.locator('[data-page="dashboard"]').click();
  }
  await p.getByRole("button", { name: "Add evidence", exact: true }).click();
  await p.locator('select[name="kind"]').selectOption("communication");
  await p.locator('input[type="file"]').setInputFiles({
    name: "synthetic-cancellation.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "Fictional Demo Alder: Membership ended on 2026-10-18. INR 1450 debit on 2026-11-04 disputed and reversal refused. This is a synthetic cancellation acknowledgment.",
    ),
  });
  const uploaded = p.waitForResponse(
    (r) => r.url().endsWith("/evidence") && r.request().method() === "POST",
  );
  await p
    .getByRole("button", { name: "Upload and extract", exact: true })
    .click();
  const changed = await (await uploaded).json();
  assert.equal(changed.assessment.scope_status, "consumer");
  assert.ok(
    changed.assessment.issue_details.some(
      (i) => i.category === "subscription_billing",
    ),
  );
  await p.locator('[data-page="dashboard"]').click();
  await p.getByRole("heading", { name: "Your situation, organised" }).waitFor();
  await p.screenshot({
    path: "runtime/unseen-subscription-dashboard.png",
    fullPage: true,
  });
  await p.locator('[data-page="story-mode"]').click();
  assert.match(
    await p.locator("#view").innerText(),
    /Fictional illustration — not a judgment/,
  );
  await p.locator('[data-page="generated-documents"]').click();
  await p.locator('select[name="kind"]').selectOption("refund_request");
  const drafted = p.waitForResponse((r) => r.url().endsWith("/draft"));
  await p
    .getByRole("button", { name: "Generate editable document", exact: true })
    .click();
  assert.equal((await drafted).status(), 200);
  await p.locator("form[data-draft]").waitFor();
  const download = p.waitForEvent("download");
  await p.getByRole("link", { name: "Download PDF", exact: true }).click();
  assert.equal(await (await download).failure(), null);
  await p.locator('[data-page="marketplace"]').click();
  await p.locator("#share-form input").check();
  const shared = p.waitForResponse((r) => r.url().endsWith("/share"));
  await p
    .getByRole("button", { name: "Share reviewed packet", exact: true })
    .click();
  assert.equal((await shared).status(), 200);
  const recipient = await b.newContext({ acceptDownloads: true });
  const lp = await recipient.newPage();
  await lp.goto(base);
  await lp.locator('[data-page="marketplace"]').click();
  await lp
    .locator("#lawyer-form input")
    .fill(fs.readFileSync("runtime/demo-lawyer-password", "utf8").trim());
  await lp
    .getByRole("button", { name: "Open demo inbox", exact: true })
    .click();
  await lp
    .getByRole("button", { name: "Acknowledge demo receipt", exact: true })
    .waitFor();
  await lp
    .getByRole("button", { name: "Acknowledge demo receipt", exact: true })
    .click();
  await lp.getByText("Demo acknowledgment recorded", { exact: true }).waitFor();
  await p.reload();
  await p
    .getByRole("heading", { name: "Your account of events", exact: true })
    .waitFor();
  await p.locator('[data-page="marketplace"]').click();
  await p
    .getByRole("button", { name: "Revoke inbox access", exact: true })
    .click();
  await p
    .getByRole("heading", { name: "Your account of events", exact: true })
    .waitFor();
  await lp.reload();
  await lp.locator('[data-page="marketplace"]').click();
  await lp
    .getByText("No voluntarily shared packets.", { exact: true })
    .waitFor();
  await p.locator('[data-page="settings"]').click();
  p.once("dialog", (d) => d.accept());
  await p
    .getByRole("button", {
      name: "Delete this case and its files",
      exact: true,
    })
    .click();
  await p.getByRole("heading", { name: "Your saved cases" }).waitFor();
  assert.deepEqual(errors, []);
  console.log(
    "PASS LIVE UNSEEN: new subscription narrative -> dynamic issues -> evidence-preserved state -> editable request -> PDF -> demo lawyer acknowledgment -> refresh -> revoke -> delete.",
  );
  if (!health.reviewed_sources)
    console.log(
      "BLOCKED: authentic statutory retrieval/legal applicability segment; approved corpus is empty.",
    );
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
