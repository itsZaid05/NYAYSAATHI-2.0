from html import escape
from weasyprint import HTML


def packet(assessment, attachments):
    a = assessment
    e = lambda x: escape(str(x))

    def listing(values):
        return "<ul>" + "".join("<li>" + e(v) + "</li>" for v in values) + "</ul>"

    body = f"<h1>NyaySaathi</h1><h2>Case preparation packet</h2><p>Case {e(a.case_id)} · {e(a.jurisdiction)} · {e(a.category)}</p>"
    body += "<p><b>Fictional demonstration. Educational preparation only. Not legal advice, not a court filing, not a prediction of outcome.</b></p>"
    body += "<h2>User allegations and document excerpts</h2>" + listing(
        f"{f.origin}: {f.text}" for f in a.facts
    )
    body += "<h2>Timeline</h2>" + listing(
        f"{t.date} — {t.description}" for t in a.timeline
    )
    body += "<h2>Missing information</h2>" + listing(a.unknowns)
    body += f"<h2>Evidence readiness: {e(a.readiness)}</h2>" + listing(
        a.readiness_flags
    )
    body += listing(
        f"{x.item}: " + ("uploaded; unverified" if x.present else "not uploaded")
        for x in a.evidence
    )
    body += "<h2>Attachment inventory</h2>" + listing(
        f"{x['filename']} ({x['kind']})" for x in attachments
    )
    body += "<h2>Verified source passages</h2>"
    if not a.sources:
        body += "<p>UNAVAILABLE. No verified law passages loaded; no legal conclusions supplied.</p>"
    for s in a.sources:
        body += f"<h3>{e(s.title)} · {e(s.provision)}</h3><blockquote>{e(s.quote)}</blockquote><p>{e(s.version)}; checked {e(s.checked_at)}<br>{e(s.url)}</p>"
    for s in a.illustrative_scenarios:
        body += f"<h2>{e(s.label)}</h2><p>{e(s.text)}</p>"
    for draft in a.drafts:
        body += f"<h2>{e(draft.status)}</h2><pre>{e(draft.content)}</pre>"
    body += "<h2>Official starting points — portal links, not filing confirmation</h2><p>National Consumer Helpline: https://consumerhelpline.gov.in/<br>e-Jagriti: https://e-jagriti.gov.in/<br>NALSA legal-aid information: https://nalsa.gov.in/</p><p>Check current eligibility, forms and procedures directly. Portal availability has not been verified in this environment.</p>"
    body += (
        "<h2>Limitations and safeguards</h2>"
        + listing(a.safety_flags)
        + f"<p>{e(a.ai_status)}. Retrieval: {e(a.retrieval_mode)}. Handoff: {e(a.handoff_status)}.</p>"
    )
    html = (
        '<html><meta charset="utf-8"><style>@page{size:A4;margin:20mm}body{font:11pt "DejaVu Sans","Noto Sans Devanagari",sans-serif;color:#243044}h1{color:#5a31f4}h2{font-size:15pt}pre{white-space:pre-wrap;font:inherit}p,li,blockquote{overflow-wrap:anywhere}</style><body>'
        + body
        + "</body></html>"
    )

    # No file/HTTP resource loading from HTML; all user text is escaped.
    def reject_url(url, *args, **kwargs):
        raise ValueError("External PDF resources are disabled")

    return HTML(string=html, url_fetcher=reject_url).write_pdf()
