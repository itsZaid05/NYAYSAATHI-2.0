"""Local, bounded extraction and reconciliation. Never authenticate evidence."""

import io
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
from backend.schemas import EvidenceAnalysis

MAX_PIXELS = 16_000_000


def ocr_image(data, mime):
    if not shutil.which("tesseract"):
        raise ValueError(
            "OCR unavailable: install Tesseract through approved package tooling"
        )
    try:
        with Image.open(io.BytesIO(data)) as image:
            if (
                image.format not in ("PNG", "JPEG")
                or {"PNG": "image/png", "JPEG": "image/jpeg"}[image.format] != mime
                or image.width * image.height > MAX_PIXELS
            ):
                raise ValueError("Unsupported image or more than 16 million pixels")
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image = image.convert("RGB")
            with tempfile.TemporaryDirectory(prefix="nyay-ocr-") as folder:
                path = Path(folder) / "input.png"
                image.save(path)
                langs = subprocess.run(
                    ["tesseract", "--list-langs"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout
                language = "eng+hin" if "hin" in langs.split() else "eng"
                result = subprocess.run(
                    ["tesseract", str(path), "stdout", "-l", language, "--psm", "6"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=True,
                )
                return result.stdout[
                    :30000
                ], f"local Tesseract OCR ({language}); errors possible"
    except (subprocess.SubprocessError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError(
            "Image/OCR failed safely; upload a clearer synthetic image or text"
        ) from None


def analyse_document(row, user_facts):
    text = row["excerpt"]
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    amounts = [
        m.group(0)
        for m in re.finditer(
            r"(?:₹\s*|INR\s*|Rs\.?\s*)\d[\d,]*(?:\.\d{1,2})?", text, re.I
        )
    ]
    refs = re.findall(
        r"(?:order|invoice|transaction|reference)\s*(?:id|number|no\.?|#)?\s*[:#=-]\s*([\w-]{3,60})",
        text,
        re.I,
    )
    pieces = [
        s.strip()[:900] for s in re.split(r"\n+|(?<=[.!?])\s+", text) if s.strip()
    ][:12]
    known_dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", user_facts))
    warnings = []
    if any(d not in known_dates for d in dates):
        warnings.append(
            "Document contains dates absent from the narrative; review and reconcile: "
            + ", ".join(sorted(set(dates) - known_dates))
        )
    if not text.strip():
        warnings.append(
            "No readable text extracted. This file cannot fill an evidence gap."
        )
    if re.search(
        r"ignore (?:all|previous)|system prompt|assistant:|forget your|reveal.*key",
        text,
        re.I,
    ):
        warnings.append(
            "Possible prompt-injection instructions detected; document treated only as untrusted text."
        )
    # Overlap suggests possible relevance, never proof of the allegation.
    support = []
    for sentence in re.split(r"(?<=[.!?।])\s+", user_facts):
        tokens = set(re.findall(r"\w{4,}", sentence.lower())) - {
            "fictional",
            "bought",
            "seller",
            "consumer",
            "this",
            "that",
            "have",
            "from",
        }
        if len(tokens & set(re.findall(r"\w{4,}", text.lower()))) >= 2:
            support.append(sentence[:1000])
    method = (
        "local Tesseract OCR; check transcription"
        if row["mime"].startswith("image/")
        else "local PDF/text extraction"
    )
    return EvidenceAnalysis(
        document_id=row["id"],
        filename=row["filename"],
        kind=row["kind"],
        extraction_method=method,
        dates=sorted(set(dates)),
        amounts=amounts[:12],
        transaction_references=refs[:12],
        relevant_excerpts=pieces,
        supports_fact_quotes=support[:8],
        warnings=warnings,
    )
