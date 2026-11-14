"use strict";
const state = {
  language: "en",
  page: "dashboard",
  assessment: null,
  health: {},
  cases: [],
  role: "guest",
  busy: false,
};
const $ = (s) => document.querySelector(s);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const t = (en, hi) => (state.language === "hi" ? hi : en);
const nav = [
  ["dashboard", "⌂", "Dashboard", "डैशबोर्ड"],
  ["intake", "◌", "Intake", "विवरण"],
  ["story-mode", "▤", "Story Mode", "कहानी"],
  ["case-summary", "≡", "Case Summary", "सारांश"],
  ["documents", "▱", "Documents", "दस्तावेज़"],
  ["generated-documents", "▧", "Generated Documents", "तैयार दस्तावेज़"],
  ["precedents", "⚖", "Case Comparison", "मामले की तुलना"],
  ["ai-insights", "✧", "Legal References", "कानूनी स्रोत"],
  ["marketplace", "♧", "Lawyers", "वकील"],
  ["policies", "◇", "Privacy", "गोपनीयता"],
  ["settings", "⚙", "Settings", "सेटिंग्स"],
  ["help", "?", "Help & Filing", "सहायता और प्रक्रिया"],
];
const sample =
  "Fictional demo: I bought a laptop online from Demo Seller on 2026-10-01 for INR 45000. The laptop would not start on 2026-10-03. I asked the seller for a replacement on 2026-10-04, but the seller refused. I have an invoice and warranty, and I want to understand my next steps.";
const sampleHi =
  "काल्पनिक उदाहरण: मैंने Demo Seller से 2026-10-01 को ऑनलाइन लैपटॉप 45000 रुपये में खरीदा। लैपटॉप 2026-10-03 को चालू नहीं हुआ। मैंने 2026-10-04 को विक्रेता से बदलने को कहा लेकिन उसने मना किया। मेरे पास बिल और वारंटी है। मुझे अगले कदम समझने हैं।";
function notice(text) {
  $("#notice").textContent = text;
}
function csrf() {
  return (
    document.cookie
      .split("; ")
      .find((v) => v.startsWith("nyay_csrf="))
      ?.split("=")[1] || ""
  );
}
async function api(path, method = "GET", data) {
  const options = { method, credentials: "same-origin", headers: {} };
  if (method !== "GET")
    options.headers["X-CSRF-Token"] = decodeURIComponent(csrf());
  if (data instanceof FormData) options.body = data;
  else if (data !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  const r = await fetch("/api" + path, options);
  if (!r.ok) {
    let message;
    try {
      const b = await r.json();
      message =
        typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail);
    } catch {
      message = await r.text().catch(() => r.statusText);
    }
    throw new Error(message || `Request failed (${r.status})`);
  }
  return r.json();
}
function button(label, action, cls = "") {
  return `<button type="button" class="${cls}" data-action="${action}">${esc(label)}</button>`;
}
function list(items) {
  return `<ul>${items.map((s) => `<li>${esc(s)}</li>`).join("")}</ul>`;
}
function empty() {
  return `<section class="card"><h2>${t("Start with your story", "अपनी बात से शुरुआत करें")}</h2><p>${t("Create a confidential fictional consumer case first.", "पहले काल्पनिक उपभोक्ता मामले का निजी कार्यक्षेत्र बनाएं।")}</p>${button(t("Open intake", "विवरण दें"), "go-intake", "primary")}</section>`;
}
function render() {
  document.documentElement.lang = state.language;
  $("#lang-en").setAttribute("aria-pressed", String(state.language === "en"));
  $("#lang-hi").setAttribute("aria-pressed", String(state.language === "hi"));
  $("#navigation").innerHTML = nav
    .map(
      ([id, icon, en, hi]) =>
        `<button type="button" data-page="${id}" ${state.page === id ? 'aria-current="page"' : ""}><span aria-hidden="true">${icon}</span>${esc(t(en, hi))}</button>`,
    )
    .join("");
  $("#page-title").textContent = t(
    nav.find((n) => n[0] === state.page)?.[2] || "Workspace",
    nav.find((n) => n[0] === state.page)?.[3] || "कार्यक्षेत्र",
  );
  $("#session-label").textContent =
    state.role === "lawyer"
      ? t("Demo lawyer account", "डेमो वकील खाता")
      : t("Confidential guest workspace", "निजी अतिथि कार्यक्षेत्र");
  $("#system-status").textContent = state.health.reviewed_sources
    ? t(
        `${state.health.reviewed_sources} reviewed passages loaded. Check individual versions and applicability.`,
        `${state.health.reviewed_sources} समीक्षित अंश उपलब्ध। संस्करण और लागू होने की जांच करें।`,
      )
    : t(
        "Verified law is unavailable: official passages have not yet passed source and rights review. Legal conclusions and statutory citations are withheld. You can still organise a fictional case, prepare a seller letter and download a packet.",
        "सत्यापित कानून उपलब्ध नहीं: आधिकारिक अंशों की स्रोत और उपयोग-अधिकार समीक्षा बाकी है। कानूनी निष्कर्ष रोके गए हैं। आप काल्पनिक मामले के तथ्य, पत्र और पैकेट तैयार कर सकते हैं।",
      );
  const profile = state.health.model_configuration;
  if (profile?.diagnostics?.length)
    $("#system-status").textContent +=
      " " +
      t("AI configuration: ", "AI कॉन्फ़िगरेशन: ") +
      profile.diagnostics.join(" ");
  if (state.health.gemini_configured && !state.health.live_ai_available) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.dataset.action = "provider-recheck";
    retry.textContent = t("Retry AI connection", "AI कनेक्शन फिर जांचें");
    retry.disabled = state.busy || state.health.provider_cooldown_seconds > 0;
    $("#system-status").append(document.createTextNode(" "), retry);
  }
  const views = {
    dashboard,
    intake,
    "case-summary": summary,
    "story-mode": story,
    documents,
    "generated-documents": generatedDocuments,
    precedents,
    "ai-insights": sources,
    marketplace: lawyers,
    policies: privacy,
    settings,
    help,
  };
  $("#view").innerHTML =
    (state.assessment ? caseRibbon() : "") + (views[state.page] || dashboard)();
  if (state.page === "documents" && state.assessment) loadDocuments();
  if (state.page === "settings" && state.assessment) loadCanonicalNarrative();
  if (state.page === "marketplace" && state.role === "lawyer") loadInbox();
}
function dashboard() {
  if (state.assessment) return activeDashboard();
  return `<section class="card hero-card"><p class="eyebrow">${t("A COMPANION FOR YOUR NEXT STEP", "आपके अगले कदम का साथी")}</p><h2>${t("You deserve to be heard. Let’s put your story in order.", "आपकी बात सुनी जानी चाहिए। आइए घटनाक्रम समझें।")}</h2><p>${t("A calm space for Indian consumer purchase and service disputes. Begin with fictional facts; keep control of every document and every share.", "भारतीय उपभोक्ता खरीद और सेवा विवादों के लिए कार्यक्षेत्र। काल्पनिक तथ्यों से शुरू करें; दस्तावेज़ और साझा करने पर नियंत्रण रखें।")}</p><div class="steps"><span>01 ${t("Intake", "विवरण")}</span><span>02 ${t("Facts & evidence", "तथ्य और साक्ष्य")}</span><span>03 ${t("Reviewed law", "समीक्षित कानून")}</span><span>04 ${t("Draft & packet", "मसौदा और पैकेट")}</span><span>05 ${t("Voluntary handoff", "स्वैच्छिक साझा")}</span></div><div class="actions">${button(t("Start a fictional case", "काल्पनिक मामला शुरू करें"), "go-intake", "primary")}${button(t("Fill laptop demonstration", "लैपटॉप उदाहरण भरें"), "sample")}</div></section>
 <div class="columns"><section class="card"><h2>${t("Your saved cases", "सहेजे हुए मामले")}</h2>${state.cases.length ? state.cases.map((c) => `<p><button data-case="${esc(c.id)}">${esc(c.category.replaceAll("_", " "))} · ${esc(c.id.slice(0, 8))}</button></p>`).join("") : `<p class="muted">${t("No cases in this session yet.", "इस सत्र में अभी कोई मामला नहीं।")}</p>`}<p class="muted">${t("Stored in the backend database, accessible with this session cookie. Session expires after 24 hours by default; case retention is capped at 7 days by default.", "बैकएंड डेटाबेस में संग्रहित। सत्र कुकी से पहुंच। सामान्यतः सत्र 24 घंटे और अधिकतम केस अवधि 7 दिन।")}</p></section><section class="card"><h2>${t("Clear boundaries", "स्पष्ट सीमाएं")}</h2><p>${t("Defective products, refunds, online shopping, warranties and services. Other legal matters receive a referral. Readiness describes evidence completeness, never chances of winning.", "खराब उत्पाद, रिफंड, ऑनलाइन खरीदारी, वारंटी और सेवाएं। अन्य कानूनी मामलों के लिए रेफरल। तैयारी केवल साक्ष्यों की पूर्णता है, जीत की संभावना नहीं।")}</p></section></div>`;
}
function intake() {
  const a = state.assessment;
  if (a)
    return `<div class="intake-layout"><section class="card"><span class="pill">${esc(a.category.replaceAll("_", " "))}</span><h2>${t("We’re listening", "हम सुन रहे हैं")}</h2><p class="muted">${esc(a.ai_status)}</p><div class="conversation" aria-live="polite">${(a
      .conversation?.length
      ? a.conversation
      : [
          {
            role: "user",
            text: a.facts
              .filter((f) => f.origin === "user_allegation")
              .map((f) => f.text)
              .join("\n"),
          },
          { role: "assistant", text: a.assistant_message },
        ]
    )
      .map(
        (turn) =>
          `<article class="chat-item ${turn.role === "assistant" ? "assistant-turn" : "user-turn"}"><small>${esc(turn.role === "assistant" ? t("NyaySaathi", "न्यायसाथी") : turn.role === "correction" ? t("Your correction", "आपका संशोधन") : t("Your allegation", "आपके बताए तथ्य"))}</small><p>${esc(turn.text)}</p></article>`,
      )
      .join(
        "",
      )}</div><div class="callout"><b>${t("Questions to clarify your story", "अपनी बात स्पष्ट करने के लिए")}</b>${list(a.unknowns)}</div><form id="message-form"><label class="field">${t("Add facts or answer a question", "तथ्य जोड़ें या सवाल का जवाब दें")}<textarea name="text" required minlength="2" maxlength="6000"></textarea></label><button class="primary" type="submit">${t("Save follow-up", "जवाब सहेजें")}</button></form><div class="actions">${button(t("Review case summary", "सारांश देखें"), "go-case-summary")}${button(t("Add evidence", "साक्ष्य जोड़ें"), "go-documents")}${button(t("Start another case", "दूसरा मामला"), "new-case")}</div></section><aside class="card context-panel"><h3>${t("What we know so far", "अब तक की जानकारी")}</h3>${entityPanel(a)}<h3>${t("Next useful action", "अगला उपयोगी कदम")}</h3><p>${esc(a.unknowns[0] || t("Review the evidence and source cards.", "साक्ष्य और स्रोत देखें।"))}</p><span class="pill">${esc(a.readiness)}</span></aside></div>`;
  return `<section class="card"><h2>${t("Tell us what happened", "बताएं क्या हुआ")}</h2><p>${t("You don’t have to know the legal language. Start with the purchase, what went wrong and the response you received. This is a demonstration: do not enter real names, contact details or confidential information.", "कानूनी भाषा जरूरी नहीं। खरीद, समस्या और मिले जवाब से शुरू करें। यह डेमो है: असली नाम, संपर्क या गोपनीय जानकारी न दें।")}</p><form id="intake-form"><label class="field">${t("Jurisdiction", "क्षेत्राधिकार")}<select name="jurisdiction"><option value="IN">India / भारत</option><option value="OTHER">Other / अन्य (referral only)</option></select></label><label class="field">${t("Your fictional narrative", "आपका काल्पनिक विवरण")}<textarea id="narrative" name="narrative" required minlength="10" maxlength="12000" rows="6"></textarea></label><div class="actions">${button(t("Use fictional laptop example", "काल्पनिक लैपटॉप उदाहरण"), "fill-sample")}</div><label class="check"><input name="processing" type="checkbox" required>${t("I consent to storing and processing this fictional case in my private backend workspace.", "मैं इस काल्पनिक मामले को निजी बैकएंड कार्यक्षेत्र में संग्रहित और प्रोसेस करने की सहमति देता/देती हूं।")}</label><label class="check"><input name="fictional" type="checkbox" required>${t("I confirm that all identities, narratives and documents are synthetic; I will not enter real confidential data.", "मैं पुष्टि करता/करती हूं कि सभी पहचान, विवरण और दस्तावेज़ काल्पनिक हैं; असली गोपनीय डेटा नहीं दूंगा/दूंगी।")}</label><label class="check"><input name="ai" type="checkbox" ${(state.health.live_ai_available ?? state.health.gemini_configured) ? "" : "disabled"}>${t("Optional: allow Gemini to process this fictional narrative. Provider terms, pricing and quotas must be reviewed by the operator.", "वैकल्पिक: Gemini को काल्पनिक विवरण प्रोसेस करने दें। संचालक को शर्तों, शुल्क और कोटा की समीक्षा करनी होगी।")}</label><p class="muted">${t("Gemini status: ", "Gemini स्थिति: ")}${(state.health.live_ai_available ?? state.health.gemini_configured) ? t("startup probe verified; provider availability can change", "स्टार्टअप जांच सफल; उपलब्धता बदल सकती है") : t("unavailable; local structured preparation only", "अनुपलब्ध; केवल स्थानीय तैयारी")}</p><button type="submit" class="primary">${t("Create confidential case", "निजी मामला बनाएं")}</button></form></section>`;
}
function summary() {
  const a = state.assessment;
  if (!a) return empty();
  return (
    intelligencePanel(a) +
    `<div class="columns"><section class="card"><h2>${t("Your account of events", "आपके बताए तथ्य")}</h2><span class="pill">${esc(a.case_id.slice(0, 8))} · ${esc(a.jurisdiction)}</span>${a.facts.map((f) => `<div class="fact"><small class="muted">${esc(f.origin)}</small><br>${esc(f.text)}</div>`).join("")}</section><section class="card"><h2>${t("Case timeline", "घटनाक्रम")}</h2>${a.timeline.length ? list(a.timeline.map((e) => `${e.date} — ${e.description}`)) : `<p>${t("No explicit ISO dates supplied. Dates are never invented.", "कोई स्पष्ट ISO तारीख नहीं मिली। तारीखें बनाई नहीं जातीं।")}</p>`}<h3>${t("Readiness", "तैयारी")}: ${esc(a.readiness)}</h3>${list(a.readiness_flags)}${readinessPanel(a)}<h3>${t("Missing information", "अधूरी जानकारी")}</h3>${list(a.unknowns)}</section></div><section class="card"><h2>${t("Boundaries and uncertainty", "सीमाएं और अनिश्चितता")}</h2>${list(a.safety_flags)}<div class="actions">${button(t("Prepare seller letter", "विक्रेता को पत्र बनाएं"), "draft", "primary")}${button(t("Download case packet PDF", "केस पैकेट PDF डाउनलोड"), "packet")}${button(t("Review sources", "स्रोत देखें"), "go-ai-insights")}</div></section>${a.drafts.length ? `<section class="card"><h2>${t("Editable seller representation", "संपादन योग्य विक्रेता पत्र")}</h2><p class="muted">${esc(a.drafts[0].status)}. ${t("Review placeholders and facts before sending privately.", "निजी तौर पर भेजने से पहले तथ्यों और खाली स्थानों की जांच करें।")}</p><form id="draft-form"><label class="field">${t("Draft text", "मसौदे का पाठ")}<textarea name="content" rows="18" maxlength="24000">${esc(a.drafts[0].content)}</textarea></label><button type="submit" class="primary">${t("Save edits", "संपादन सहेजें")}</button></form></section>` : ""}`
  );
}
function story() {
  const a = state.assessment;
  if (!a) return empty();
  return `<section class="card"><h2>${t("A story to make the next step clearer", "अगला कदम समझाने वाली कहानी")}</h2><p>${t("Original fictional scenarios are selected for this case. They are learning aids, never judgments or predictions.", "इस मामले के लिए चुने मूल काल्पनिक उदाहरण। ये शैक्षिक हैं, निर्णय या भविष्यवाणी नहीं।")}</p>${a.illustrative_scenarios.map((x) => `<article class="story-card"><span class="pill">${esc(x.label)}</span><h3>${esc(x.title)}</h3><p>${esc(x.text)}</p><div class="columns"><div><h4>${t("Similarities", "समानताएं")}</h4><p>${esc(x.similarities)}</p></div><div><h4>${t("Differences & uncertainty", "अंतर और अनिश्चितता")}</h4><p>${esc(x.differences)}</p></div></div>${list(x.lessons || [])}<p class="muted">${x.source_ids?.length ? esc(t("Related reviewed sources: ", "संबंधित समीक्षित स्रोत: ") + x.source_ids.join(", ")) : t("No reviewed law attached to this story; legal interpretation is withheld.", "इस कहानी से जुड़ा समीक्षित कानून उपलब्ध नहीं; कानूनी निष्कर्ष रोके गए हैं।")}</p></article>`).join("") || t("Story mode is unavailable outside supported disputes.", "अन्य विवादों में कहानी उपलब्ध नहीं।")}</section>`;
}
function documents() {
  const a = state.assessment;
  if (!a) return empty();
  return `<section class="card"><h2>${t("Evidence, one piece at a time", "एक-एक करके साक्ष्य")}</h2>${list(a.evidence.map((e) => `${e.present ? "✓" : "○"} ${e.item} — ${e.reason}`))}<form id="evidence-form"><label class="field">${t("Document category", "दस्तावेज़ का प्रकार")}<select name="kind"><option value="invoice">Invoice / बिल</option><option value="fault">Fault description / खराबी</option><option value="communication">Seller correspondence / पत्राचार</option><option value="warranty">Warranty / वारंटी</option><option value="other">Other / अन्य</option></select></label><label class="field">${t("Synthetic TXT, PDF, PNG or JPEG, up to 5 MB", "काल्पनिक TXT, PDF, PNG या JPEG, अधिकतम 5 MB")}<input name="file" type="file" accept=".txt,.pdf,.png,.jpg,.jpeg" required></label><p class="muted">${t("Local text extraction and bounded Tesseract image OCR. Transcription can be wrong; review extracted facts. No authenticity or malware guarantee. Synthetic documents only.", "स्थानीय पाठ निष्कर्षण और Tesseract OCR उपलब्ध। पढ़े गए पाठ में गलती हो सकती है; जांचें। प्रामाणिकता या मैलवेयर सुरक्षा की गारंटी नहीं। केवल काल्पनिक दस्तावेज़।")}</p><button type="submit" class="primary">${t("Upload and extract", "अपलोड और पाठ निकालें")}</button></form><div id="documents-list" aria-live="polite"></div></section>`;
}
function sources() {
  const a = state.assessment;
  if (!a) return empty();
  return `<section class="card"><h2>${t("Trace every legal reference", "हर कानूनी स्रोत जांचें")}</h2><p class="muted">${esc(a.retrieval_mode)} · ${esc(a.ai_status)}</p>${a.sources.length ? a.sources.map((s) => `<article class="source-card"><h3>${esc(s.title)} · ${esc(s.provision)}</h3><blockquote>${esc(s.quote)}</blockquote><p>${esc(s.version)} · ${t("Checked", "जांच")}: ${esc(s.checked_at)}</p><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${t("Open official source", "आधिकारिक स्रोत खोलें")}</a></article>`).join("") : `<div class="callout">${t("No reviewed legal passages available. We cannot responsibly identify applicable sections or deadlines. Official starting points are in Help; they are not substitutes for a reviewed legal assessment.", "समीक्षित कानूनी अंश उपलब्ध नहीं। लागू धाराएं या समय-सीमा नहीं बता सकते। सहायता में आधिकारिक पोर्टल हैं; वे कानूनी आकलन का विकल्प नहीं।")}</div>`}${a.options.map((o) => `<article class="source-card"><h3>${esc(o.action)}</h3><blockquote>${esc(o.proposition)}</blockquote><p>${esc(o.conditions)} ${esc(o.caveats)}</p><small>${esc(o.source_ids.join(", "))}</small></article>`).join("")}</section>`;
}
function lawyers() {
  if (state.role === "lawyer")
    return `<section class="card"><h2>${t("Demo lawyer inbox", "डेमो वकील इनबॉक्स")}</h2><p>${t("Demonstration account, not a verified advocate. Only voluntarily shared packet snapshots appear here.", "डेमो खाता, सत्यापित अधिवक्ता नहीं। केवल स्वेच्छा से साझा पैकेट दिखते हैं।")}</p><div id="inbox"></div></section>`;
  const a = state.assessment;
  return `<section class="card"><h2>${t("Share only when you choose", "अपनी इच्छा से साझा करें")}</h2><span class="pill">${t("Demonstration lawyer — not a verified advocate", "डेमो वकील — सत्यापित अधिवक्ता नहीं")}</span><p>${t("A private demo inbox demonstrates document handoff. No lawyer contact, professional representation, email or government filing is implied. The recipient receives a PDF snapshot, not ongoing access to your workspace.", "निजी डेमो इनबॉक्स दस्तावेज़ साझा करना दिखाता है। वकील संपर्क, प्रतिनिधित्व, ईमेल या सरकारी दाखिला नहीं। प्राप्तकर्ता को PDF प्रति मिलती है, पूरे कार्यक्षेत्र की पहुंच नहीं।")}</p>${a ? `<p>${t("Current handoff", "वर्तमान स्थिति")}: ${esc(a.handoff_status)}</p><form id="share-form"><label class="check"><input name="share" type="checkbox" required>${t("I have reviewed my fictional case packet and explicitly consent to sharing this snapshot with the demo lawyer inbox.", "मैंने काल्पनिक केस पैकेट जांचा है और डेमो वकील इनबॉक्स में इस प्रति को साझा करने की स्पष्ट सहमति देता/देती हूं।")}</label><button type="submit" class="primary" ${state.health.lawyer_enabled ? "" : "disabled"}>${t("Share reviewed packet", "जांचा पैकेट साझा करें")}</button></form><div class="actions">${button(t("Download to review first", "पहले डाउनलोड कर जांचें"), "packet")}${button(t("Revoke inbox access", "इनबॉक्स पहुंच हटाएं"), "revoke")}</div>` : empty()}${!state.health.lawyer_enabled ? `<p class="callout">${t("Handoff disabled: operator must configure a private demo lawyer password.", "साझा करना बंद है: संचालक को निजी डेमो वकील पासवर्ड कॉन्फ़िगर करना होगा।")}</p>` : ""}</section><section class="card"><h2>${t("Demo lawyer sign-in", "डेमो वकील प्रवेश")}</h2><p class="muted">${t("Use a separate browser profile for the lawyer so the guest session remains available.", "अतिथि सत्र सुरक्षित रखने के लिए वकील हेतु अलग ब्राउज़र प्रोफ़ाइल उपयोग करें।")}</p><form id="lawyer-form"><label class="field">${t("Private demo password", "निजी डेमो पासवर्ड")}<input name="password" type="password" required autocomplete="current-password"></label><button type="submit">${t("Open demo inbox", "डेमो इनबॉक्स खोलें")}</button></form></section>`;
}
function privacy() {
  return `<section class="card"><h2>${t("Your information, your choice", "आपकी जानकारी, आपकी पसंद")}</h2>${list([t("This is a fictional-data demonstrator. Do not enter real confidential legal narratives or personal documents.", "यह काल्पनिक डेटा डेमो है। असली गोपनीय कानूनी विवरण या निजी दस्तावेज़ न दें।"), t("Case state and uploaded files are stored in an access-controlled server-side SQLite database. Session cookies are HttpOnly; CSRF tokens protect mutations.", "मामले और फाइलें सर्वर के नियंत्रित SQLite डेटाबेस में हैं। HttpOnly सत्र कुकी और CSRF सुरक्षा है।"), t("Gemini receives a narrative only after separate opt-in and operator configuration. Document extraction is local. Redaction is best-effort, not a privacy guarantee.", "अलग सहमति और कॉन्फ़िगरेशन पर ही Gemini को विवरण मिलता है। दस्तावेज़ का पाठ स्थानीय रूप से निकलता है। पहचान हटाना पूर्ण गोपनीयता की गारंटी नहीं।"), t("Sessions expire after 24 hours by default; cases are removed at expiry or within the configured retention period (default 7 days). Cleanup runs on startup and authenticated requests. Backups and downloaded copies require separate handling.", "सामान्यतः सत्र 24 घंटे में समाप्त होता है; मामले अधिकतम 7 दिन में या सत्र समाप्ति पर हटते हैं। सफाई स्टार्टअप और प्रमाणित अनुरोधों पर चलती है। बैकअप और डाउनलोड प्रति अलग संभालें।"), t("Sharing is optional and logged. Revocation removes inbox access but cannot recall copies already downloaded. Case deletion also removes evidence and handoffs.", "साझा करना वैकल्पिक और दर्ज होता है। पहुंच हटाने पर डाउनलोड प्रति नहीं मिटती। मामला हटाने पर साक्ष्य और इनबॉक्स प्रति भी हटती है।")])}</section>`;
}
function settings() {
  const a = state.assessment;
  const extra = a
    ? `<section class="card"><h2>${t("Correct your facts", "अपने तथ्य सुधारें")}</h2><p>${t("Replace the canonical narrative to correct a mistake. Earlier conversation is retained and labelled; assessments use the corrected account.", "गलती सुधारने के लिए मुख्य विवरण बदलें। पुराना इतिहास चिन्हित रहता है; आकलन संशोधित विवरण उपयोग करता है।")}</p><form id="correction-form"><label class="field">${t("Corrected fictional account", "सुधरा काल्पनिक विवरण")}<textarea name="narrative" required minlength="10" maxlength="30000" rows="8">${esc(
        a.facts
          .filter((f) => f.origin === "user_allegation")
          .map((f) => f.text)
          .join("\n"),
      )}</textarea></label><button type="submit">${t("Save corrected facts", "सुधरे तथ्य सहेजें")}</button></form></section><section class="card"><h2>${t("AI processing consent", "AI प्रोसेसिंग सहमति")}</h2><form id="ai-consent-form"><label class="check"><input name="allow" type="checkbox" ${a.consent.ai_processing ? "checked" : ""}>${t("Allow this synthetic case context to be processed by the configured Gemini provider.", "इस काल्पनिक विवरण को कॉन्फ़िगर Gemini प्रदाता से प्रोसेस करने दें।")}</label><button type="submit">${t("Update AI consent", "AI सहमति बदलें")}</button></form></section>`
    : "";
  return (
    extra +
    `<section class="card"><h2>${t("Workspace controls", "कार्यक्षेत्र नियंत्रण")}</h2><div class="actions">${button("English", "english")}${button("हिंदी", "hindi")}${button(t("Start another fictional case", "दूसरा काल्पनिक मामला"), "new-case")}${state.assessment ? button(t("Delete this case and its files", "यह मामला और फाइलें हटाएं"), "delete", "danger") : ""}</div><p class="muted">${t("Deleting is permanent on this server. Existing downloaded copies remain outside its control.", "हटाना इस सर्वर पर स्थायी है। डाउनलोड प्रतियां इसके नियंत्रण से बाहर हैं।")}</p>${button(t("View consent and sharing audit", "सहमति और साझा करने का रिकॉर्ड"), "audit")}<div id="audit"></div></section>`
  );
}
function help() {
  return `<section class="card"><h2>${t("Official starting points", "आधिकारिक शुरुआती पोर्टल")}</h2><p>${t("These links are official portals, not confirmation of current eligibility, deadlines, an integration or a completed filing. Review current instructions directly before acting.", "ये आधिकारिक पोर्टल हैं, पात्रता, समय-सीमा, एकीकरण या दाखिले की पुष्टि नहीं। कार्रवाई से पहले वर्तमान निर्देश स्वयं जांचें।")}</p><ul><li><a href="https://consumerhelpline.gov.in/" target="_blank" rel="noopener noreferrer">National Consumer Helpline</a> — ${t("review available grievance assistance and current submission instructions.", "शिकायत सहायता और वर्तमान निर्देश देखें।")}</li><li><a href="https://e-jagriti.gov.in/" target="_blank" rel="noopener noreferrer">e-Jagriti</a> — ${t("review consumer-commission filing requirements, forms and forum instructions. A seller letter is not a commission complaint.", "उपभोक्ता आयोग के फॉर्म और दाखिले के निर्देश देखें। विक्रेता को पत्र आयोग की शिकायत नहीं।")}</li><li><a href="https://indiacode.gov.in/" target="_blank" rel="noopener noreferrer">India Code</a> — ${t("consult official legislation and current amendments.", "आधिकारिक कानून और वर्तमान संशोधन देखें।")}</li><li><a href="https://nalsa.gov.in/" target="_blank" rel="noopener noreferrer">NALSA Legal Aid</a> — ${t("check legal-aid eligibility and access information for unsupported matters.", "अन्य मामलों के लिए विधिक सहायता की पात्रता और पहुंच देखें।")}</li></ul><p>${t("Bring your purchase record, dated event summary, correspondence and desired remedy. Do not rely on this app for limitation calculations or forum selection.", "खरीद रिकॉर्ड, तारीख सहित विवरण, पत्राचार और मांगा समाधान तैयार रखें। समय-सीमा या आयोग चुनने के लिए इस ऐप पर निर्भर न रहें।")}</p></section>`;
}
async function loadDocuments() {
  try {
    const rows = await api(`/cases/${state.assessment.case_id}/evidence`);
    if (!$("#documents-list")) return;
    $("#documents-list").innerHTML = rows
      .map(
        (d) =>
          `<article class="source-card"><h3>${esc(d.filename)}</h3><p>${esc(d.kind)}</p><a class="action" href="/api/cases/${state.assessment.case_id}/evidence/${esc(d.id)}">${t("Download original", "मूल डाउनलोड")}</a><pre class="document-text">${esc(d.excerpt)}</pre>${evidenceDetails(d.id)}${list(d.warnings)}</article>`,
      )
      .join("");
  } catch (e) {
    notice(e.message);
  }
}
async function loadInbox() {
  try {
    const rows = await api("/lawyer/inbox");
    if (!$("#inbox")) return;
    $("#inbox").innerHTML = rows.length
      ? rows
          .map(
            (c) =>
              `<article class="source-card"><h3>${esc(c.case_id.slice(0, 8))}</h3><p>${c.reviewed ? "Demo acknowledgment recorded" : "Awaiting demo acknowledgment"}</p><a class="action" href="/api/lawyer/inbox/${esc(c.case_id)}/packet.pdf">Download shared snapshot</a><button data-review="${esc(c.case_id)}">Acknowledge demo receipt</button></article>`,
          )
          .join("")
      : "<p>No voluntarily shared packets.</p>";
  } catch (e) {
    notice(e.message);
  }
}
async function updateCases() {
  state.cases = await api("/cases");
}
async function openCase(id) {
  state.assessment = await api(`/cases/${id}/assessment`);
  state.language = state.assessment.language;
  sessionStorage.setItem("nyay_case", id);
  state.page = "case-summary";
  render();
}
async function action(name) {
  if (name === "provider-recheck") {
    const intake = $("#intake-form");
    const draft = intake
      ? {
          narrative: intake.elements.narrative.value,
          jurisdiction: intake.elements.jurisdiction.value,
          processing: intake.elements.processing.checked,
          fictional: intake.elements.fictional.checked,
        }
      : null;
    state.health = await api("/provider/recheck", "POST");
    render();
    if (draft && $("#intake-form")) {
      const f = $("#intake-form");
      f.elements.narrative.value = draft.narrative;
      f.elements.jurisdiction.value = draft.jurisdiction;
      f.elements.processing.checked = draft.processing;
      f.elements.fictional.checked = draft.fictional;
    }
    notice(
      state.health.live_ai_available
        ? t("AI connectivity verified.", "AI कनेक्शन जांच सफल।")
        : t(
            "AI remains unavailable; see the provider diagnosis.",
            "AI अभी अनुपलब्ध; प्रदाता का निदान देखें।",
          ),
    );
    return;
  }
  if (name.startsWith("go-")) {
    state.page = name.slice(3);
    render();
    return;
  }
  if (name === "english" || name === "hindi") {
    await setLanguage(name === "english" ? "en" : "hi");
    return;
  }
  if (name === "sample" || name === "fill-sample") {
    if (name === "sample") {
      state.assessment = null;
      state.page = "intake";
      render();
    }
    $("#narrative").value = state.language === "hi" ? sampleHi : sample;
    return;
  }
  if (name === "new-case") {
    state.assessment = null;
    sessionStorage.removeItem("nyay_case");
    state.page = "intake";
    render();
    return;
  }
  const a = state.assessment;
  if (name === "edit-draft") {
    state.page = "generated-documents";
    render();
    return;
  }
  if (!a) throw new Error(t("Open a case first.", "पहले मामला खोलें।"));
  if (name === "analyse") {
    state.assessment = await api(`/cases/${a.case_id}/analyse`, "POST");
    render();
    return;
  }
  if (name === "draft") {
    state.assessment = await api(`/cases/${a.case_id}/draft`, "POST", {});
    state.page = "case-summary";
    render();
  }
  if (name === "packet") {
    const link = await api(`/cases/${a.case_id}/packet-link`, "POST");
    const anchor = document.createElement("a");
    anchor.href = link.url;
    anchor.download = "nyaysaathi-case-packet.pdf";
    anchor.click();
    notice(
      t(
        "Packet requested. Check your downloads; this is not a filing.",
        "पैकेट अनुरोधित। डाउनलोड जांचें; यह दाखिला नहीं है।",
      ),
    );
  }
  if (name === "revoke") {
    await api(`/cases/${a.case_id}/revoke`, "POST");
    await openCase(a.case_id);
    notice(
      t(
        "Demo inbox access revoked. Downloaded copies cannot be recalled.",
        "डेमो इनबॉक्स पहुंच हटाई गई। डाउनलोड प्रति नहीं मिट सकती।",
      ),
    );
  }
  if (name === "delete") {
    if (
      !confirm(
        t(
          "Permanently delete this case, evidence and handoff?",
          "मामला, साक्ष्य और साझा प्रति स्थायी रूप से हटाएं?",
        ),
      )
    )
      return;
    await api(`/cases/${a.case_id}`, "DELETE");
    state.assessment = null;
    sessionStorage.removeItem("nyay_case");
    await updateCases();
    state.page = "dashboard";
    render();
    notice(t("Case deleted from the server.", "मामला सर्वर से हटाया गया।"));
  }
  if (name === "audit") {
    const rows = await api(`/cases/${a.case_id}/audit`);
    $("#audit").innerHTML = list(
      rows.map(
        (r) =>
          `${new Date(r.created_at * 1000).toLocaleString()} — ${r.action}`,
      ),
    );
  }
}
async function submit(form) {
  const data = new FormData(form),
    id = state.assessment?.case_id;
  if (form.id === "intake-form") {
    state.assessment = await api("/cases/intake", "POST", {
      narrative: data.get("narrative"),
      jurisdiction: data.get("jurisdiction"),
      language: state.language,
      consent: {
        processing: data.has("processing"),
        fictional_demo: data.has("fictional"),
        ai_processing: data.has("ai"),
        sharing: false,
      },
    });
    sessionStorage.setItem("nyay_case", state.assessment.case_id);
    await updateCases();
    state.page = "intake";
    render();
  }
  if (form.id === "message-form") {
    state.assessment = await api(`/cases/${id}/message`, "POST", {
      text: data.get("text"),
    });
    render();
  }
  if (form.id === "evidence-form") {
    const result = await api(`/cases/${id}/evidence`, "POST", data);
    state.assessment = result.assessment;
    render();
    notice(
      `${result.characters_extracted} ${t("characters extracted locally. ", "अक्षर स्थानीय रूप से निकले। ")}${result.warnings.join(" ")}`,
    );
  }
  if (form.id === "draft-form" || form.dataset.draft) {
    state.assessment = await api(`/cases/${id}/draft`, "POST", {
      content: data.get("content"),
      kind:
        data.get("kind") ||
        state.assessment.drafts[0]?.kind ||
        "seller_representation",
    });
    render();
    notice(
      t("Draft edits saved to the database.", "मसौदा डेटाबेस में सहेजा गया।"),
    );
  }
  if (form.id === "share-form") {
    const result = await api(`/cases/${id}/share`, "POST", {
      consent: data.has("share"),
    });
    state.assessment = await api(`/cases/${id}/assessment`);
    render();
    notice(result.notice);
  }
  if (form.id === "correction-form") {
    state.assessment = await api(`/cases/${id}/context`, "PATCH", {
      narrative: data.get("narrative"),
    });
    render();
    notice(
      t(
        "Canonical facts corrected. Old turns remain labelled in history.",
        "मुख्य तथ्य संशोधित। पुराने संदेश इतिहास में चिन्हित रहते हैं।",
      ),
    );
  }
  if (form.id === "generate-form") {
    state.assessment = await api(`/cases/${id}/draft`, "POST", {
      kind: data.get("kind"),
    });
    render();
  }
  if (form.id === "ai-consent-form") {
    state.assessment = await api(`/cases/${id}/consent`, "PATCH", {
      ai_processing: data.has("allow"),
    });
    render();
    notice(t("AI consent updated.", "AI सहमति बदली गई।"));
  }
  if (form.id === "lawyer-form") {
    await api("/lawyer/login", "POST", { password: data.get("password") });
    state.role = "lawyer";
    state.cases = [];
    state.assessment = null;
    sessionStorage.removeItem("nyay_case");
    render();
  }
}
async function run(operation) {
  if (state.busy) return;
  state.busy = true;
  notice(
    t(
      "Working… your case stays saved if this request fails.",
      "प्रक्रिया जारी है… अनुरोध विफल होने पर भी मामला सहेजा रहता है।",
    ),
  );
  document.body.setAttribute("aria-busy", "true");
  try {
    await operation();
    if (
      $("#notice").textContent.startsWith("Working") ||
      $("#notice").textContent.startsWith("प्रक्रिया जारी")
    )
      notice("");
  } catch (e) {
    notice(e.message);
  } finally {
    state.busy = false;
    document.body.setAttribute("aria-busy", "false");
    const retry = $('[data-action="provider-recheck"]');
    if (retry) {
      retry.disabled = state.health.provider_cooldown_seconds > 0;
      if (retry.disabled)
        setTimeout(
          () => {
            state.health.provider_cooldown_seconds = 0;
            const current = $('[data-action="provider-recheck"]');
            if (current) current.disabled = false;
          },
          (state.health.provider_cooldown_seconds + 1) * 1000,
        );
    }
  }
}
document.addEventListener("click", (event) => {
  const b = event.target.closest("button");
  if (!b) return;
  if (b.dataset.page) {
    state.page = b.dataset.page;
    notice("");
    render();
  } else if (b.dataset.action) run(() => action(b.dataset.action));
  else if (b.dataset.case) run(() => openCase(b.dataset.case));
  else if (b.dataset.review)
    run(async () => {
      await api(`/lawyer/inbox/${b.dataset.review}/review`, "POST");
      await loadInbox();
    });
});
document.addEventListener("submit", (event) => {
  event.preventDefault();
  run(() => submit(event.target));
});
async function setLanguage(language) {
  if (state.assessment)
    state.assessment = await api(
      `/cases/${state.assessment.case_id}/context`,
      "PATCH",
      { language },
    );
  state.language = language;
  render();
}
$("#lang-en").addEventListener("click", () => run(() => setLanguage("en")));
$("#lang-hi").addEventListener("click", () => run(() => setLanguage("hi")));

function evidenceDetails(id) {
  const d = state.assessment?.evidence_analysis?.find(
    (d) => d.document_id === id,
  );
  if (!d) return "";
  return `<details><summary>${t("Extracted document information", "दस्तावेज़ से निकली जानकारी")}</summary><p class="muted">${esc(d.extraction_method)}</p><dl class="entity-list"><dt>${t("Dates", "तारीखें")}</dt><dd>${esc(d.dates.join(", ") || "—")}</dd><dt>${t("Amounts", "राशियां")}</dt><dd>${esc(d.amounts.join(", ") || "—")}</dd><dt>${t("Transaction references", "लेनदेन संदर्भ")}</dt><dd>${esc(d.transaction_references.join(", ") || "—")}</dd></dl><h4>${t("Potentially related user allegations — not proof", "संभावित संबंधित आरोप — प्रमाण नहीं")}</h4>${list(d.supports_fact_quotes)}</details>`;
}
async function loadCanonicalNarrative() {
  try {
    const data = await api(`/cases/${state.assessment.case_id}/context`);
    const field = $("#correction-form textarea");
    if (field && field.value === field.defaultValue)
      field.value = data.narrative;
  } catch (e) {
    notice(e.message);
  }
}
function caseRibbon() {
  const a = state.assessment;
  return `<div class="case-ribbon"><div><span class="eyebrow">${t("ACTIVE CASE", "चुना मामला")}</span><b>${esc(a.category.replaceAll("_", " "))}</b><small>${esc(a.case_id.slice(0, 8))} · ${esc(a.jurisdiction)}</small></div><span class="pill">${esc(a.readiness)}</span><span>${a.evidence_analysis?.length || 0} ${t("documents", "दस्तावेज़")}</span><span>${a.sources.length} ${t("source passages", "स्रोत अंश")}</span></div>`;
}
function entityPanel(a) {
  return `<dl class="entity-list"><dt>${t("Parties (alleged)", "पक्ष (बताए गए)")}</dt><dd>${esc(a.parties?.map((p) => p.value).join(", ") || t("Not yet identified", "अभी अस्पष्ट"))}</dd><dt>${t("Amount stated", "बताई राशि")}</dt><dd>${esc(a.amounts?.map((x) => x.value).join(", ") || t("Not provided", "उपलब्ध नहीं"))}</dd><dt>${t("Requested resolution", "मांगा समाधान")}</dt><dd>${esc(a.desired_remedy || t("Please clarify", "स्पष्ट करें"))}</dd></dl>`;
}
function readinessPanel(a) {
  return `<div class="readiness-findings">${(a.readiness_findings || []).map((f) => `<details><summary><span class="status-dot ${f.status}"></span>${esc(f.dimension)} · ${esc(f.status.replaceAll("_", " "))}</summary><p>${esc(f.finding)}</p></details>`).join("")}</div>`;
}
function intelligencePanel(a) {
  return `<section class="card intelligence-panel"><p class="eyebrow">${t("CASE INTELLIGENCE", "मामले की समझ")}</p><h2>${t("Your situation, organised", "आपकी स्थिति, व्यवस्थित")}</h2><div class="columns"><div>${entityPanel(a)}</div><div><h3>${t("Issues to examine", "समझने योग्य मुद्दे")}</h3>${list(a.issues)}<p class="muted">${esc(a.understanding_method || "Local fallback")}</p>${(a.issue_details || []).map((i) => `<details class="issue-detail"><summary>${esc(i.title)}</summary><p><b>${t("User allegations", "उपयोगकर्ता के बताए तथ्य")}</b></p>${list(i.fact_quotes)}<p><b>${t("Suggested evidence", "सुझाए साक्ष्य")}</b></p>${list(i.evidence_needed)}${list(i.unresolved_facts)}</details>`).join("")}<p class="muted">${esc(a.ai_status)}</p><div class="actions">${button(t("Update AI analysis", "AI विश्लेषण अपडेट"), "analyse", "primary")}${button(t("Prepare documents", "दस्तावेज़ तैयार करें"), "go-generated-documents")}</div></div></div>${a.legal_analysis ? `<p>${esc(a.legal_analysis.overview)} ${esc(a.legal_validation_notice || "")}</p>${a.legal_analysis.claims.map((c) => `<article class="analysis-claim"><span class="pill">${t("AI interpretation · citations checked · legal review pending", "AI व्याख्या · संदर्भ जांचे · कानूनी समीक्षा बाकी")}</span><h3>${esc(c.proposition)}</h3><p>${esc(c.application)}</p><h4>${t("Conditions and unknowns", "शर्तें और अधूरे तथ्य")}</h4>${list(c.conditions.concat(c.unknowns))}<p><b>${t("Suggested action", "सुझाया कदम")}:</b> ${esc(c.suggested_action)}</p><p class="muted">${esc(c.qualification)} · ${esc(c.source_ids.join(", "))}</p></article>`).join("")}` : `<div class="callout">${t("No legal interpretation has passed the live source-support workflow. Facts and preparation remain available.", "कोई कानूनी व्याख्या स्रोत-समर्थन प्रक्रिया से स्वीकृत नहीं हुई। तथ्य और तैयारी उपलब्ध हैं।")}</div>`}</section>`;
}
function activeDashboard() {
  const a = state.assessment;
  return (
    intelligencePanel(a) +
    `<div class="columns"><section class="card"><h2>${t("Next useful steps", "अगले उपयोगी कदम")}</h2>${list(a.unknowns)}<div class="actions">${button(t("Continue conversation", "बात जारी रखें"), "go-intake")}${button(t("Organise evidence", "साक्ष्य व्यवस्थित करें"), "go-documents")}</div></section><section class="card"><h2>${t("Preparation findings", "तैयारी की स्थिति")}</h2>${readinessPanel(a)}</section></div>`
  );
}
function generatedDocuments() {
  const a = state.assessment;
  if (!a) return empty();
  const kinds = [
    ["seller_representation", "Seller representation", "विक्रेता को पत्र"],
    [
      "refund_request",
      "Refund / replacement request",
      "रिफंड / बदलने का अनुरोध",
    ],
    ["grievance_summary", "Grievance summary", "शिकायत सारांश"],
    ["chronology", "Case chronology", "घटनाक्रम"],
    ["evidence_inventory", "Evidence inventory", "साक्ष्य सूची"],
    ["lawyer_brief", "Lawyer consultation brief", "वकील परामर्श विवरण"],
  ];
  return `<section class="card"><h2>${t("Prepare something useful", "उपयोगी दस्तावेज़ बनाएं")}</h2><p>${t("Every template uses your current case facts. Check placeholders before sending. These documents are not filed complaints or lawyer-reviewed pleadings.", "हर टेम्पलेट वर्तमान तथ्यों से बनता है। भेजने से पहले खाली स्थान जांचें। ये दाखिल शिकायत या वकील-समीक्षित दस्तावेज़ नहीं।")}</p><form id="generate-form"><label class="field">${t("Document type", "दस्तावेज़ प्रकार")}<select name="kind">${kinds.map(([id, en, hi]) => `<option value="${id}">${esc(t(en, hi))}</option>`).join("")}</select></label><button class="primary" type="submit">${t("Generate editable document", "संपादन योग्य दस्तावेज़ बनाएं")}</button></form></section>${a.drafts.map((d) => `<section class="card"><h3>${esc(kinds.find((k) => k[0] === d.kind)?.[state.language === "hi" ? 2 : 1] || d.kind)}</h3><p class="muted">${esc(d.status)}</p><form id="draft-form-${d.id}" data-draft="true"><input type="hidden" name="kind" value="${esc(d.kind)}"><label class="field">${t("Editable content", "संपादन योग्य पाठ")}<textarea name="content" rows="15" maxlength="24000">${esc(d.content)}</textarea></label><button type="submit">${t("Save edits", "संपादन सहेजें")}</button></form><div class="actions"><a class="action" href="/api/cases/${a.case_id}/drafts/${d.id}.txt">${t("Download text", "पाठ डाउनलोड")}</a><a class="action" href="/api/cases/${a.case_id}/drafts/${d.id}.pdf">${t("Download PDF", "PDF डाउनलोड")}</a></div></section>`).join("")}`;
}
function precedents() {
  return `<section class="card"><span class="pill">${t("Authentic judgments: unavailable", "असली निर्णय: अनुपलब्ध")}</span><h2>${t("Comparison without invented precedents", "बिना काल्पनिक मिसालों के तुलना")}</h2><p>${t("No authorised, independently validated judgment corpus is connected. Court, decision date, genuine citation, legal principle and comparison limits are required before this provider can be enabled. UK retrieval remains disabled pending licensing and jurisdiction review.", "अधिकृत, स्वतंत्र सत्यापित निर्णय संग्रह जुड़ा नहीं है। सक्षम करने से पहले अदालत, तारीख, असली संदर्भ, सिद्धांत और तुलना की सीमाएं जरूरी हैं। UK प्रदाता लाइसेंस और क्षेत्राधिकार समीक्षा तक बंद है।")}</p>${button(t("Explore fictional learning scenarios", "काल्पनिक शैक्षिक उदाहरण देखें"), "go-story-mode")}</section>`;
}
async function init() {
  try {
    state.health = await api("/health");
    try {
      state.role = (await api("/session")).role;
    } catch {
      await api("/session", "POST");
    }
    await updateCases();
    const saved = sessionStorage.getItem("nyay_case");
    if (saved && state.cases.some((c) => c.id === saved)) await openCase(saved);
    else render();
  } catch (e) {
    render();
    notice(t("Backend unavailable: ", "बैकएंड अनुपलब्ध: ") + e.message);
  }
}
init();
