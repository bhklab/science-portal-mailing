"""
Batch extraction runner for eval papers.

Usage (from science-portal-mailing/):
    python llm_pipeline/run_batch.py
    python llm_pipeline/run_batch.py --model gemini-3.1-flash-lite
    python llm_pipeline/run_batch.py --force   # re-run even if output exists
"""

import argparse
import asyncio
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from test_extraction import (
    fetch_crossref,
    fetch_gemini,
    fetch_page_links,
    classify_page_links,
    crawl_other_links,
    merge_supplementary,
    DEFAULT_MODEL,
    MODELS,
)

MANIFEST_PATH = HERE / "eval_manifest.json"


async def run_paper(entry: dict, model: str, force: bool) -> None:
    pdf_path = ROOT / entry["pdf"]
    output_path = ROOT / entry["output"]
    doi = entry["doi"]
    url = entry.get("url")

    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return

    if output_path.exists() and not force:
        print(f"[SKIP] {pdf_path.name} — output already exists")
        return

    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path.name}  |  DOI: {doi}")
    if url:
        print(f"URL: {url}")
    print(f"{'='*60}")

    t_crossref = time.time()
    crossref_data = fetch_crossref(doi)
    crossref_elapsed = round(time.time() - t_crossref, 1)

    gemini_pdf, pdf_timing = fetch_gemini(pdf_path, model)

    # Page scraping (only if url is provided in manifest) — best-effort, never fatal
    page_supplementary = None
    page_timing = {}
    if url:
        try:
            links_text, page_scrape_s = await fetch_page_links(url)
            page_supplementary, page_timing = classify_page_links(links_text, model)
            page_timing["page_scrape_s"] = page_scrape_s
        except Exception as e:
            print(f"[WARN] Page scraping failed for {url} ({e!r}) — falling back to PDF-only extraction")

    # Crawl otherLinks that look like project/resource-index sites — best-effort
    already_crawled = {url} if url else set()
    other_link_supplementary, other_link_timings = await crawl_other_links(
        gemini_pdf.otherLinks, model, already_crawled
    )

    merged_supplementary = gemini_pdf.supplementary
    if page_supplementary:
        merged_supplementary = merge_supplementary(merged_supplementary, page_supplementary)
    if other_link_supplementary:
        merged_supplementary = merge_supplementary(merged_supplementary, other_link_supplementary)

    final = gemini_pdf.model_dump()
    final["date"] = crossref_data["date"]
    final["type"] = crossref_data["type"]
    final["publisher"] = crossref_data["publisher"]
    final["citations"] = crossref_data["citations"]
    final["supplementary"] = merged_supplementary.model_dump()

    output = {
        "doi": doi,
        "pdf": str(pdf_path),
        "url": url,
        "model": model,
        "timing": {
            "crossref_s": crossref_elapsed,
            "gemini_pdf_upload_s": pdf_timing["upload_s"],
            "gemini_pdf_inference_s": pdf_timing["inference_s"],
            "gemini_pdf_total_s": pdf_timing["total_s"],
            **({"page_scrape_s": page_timing["page_scrape_s"],
                "gemini_page_s": page_timing["page_classify_s"]} if page_timing else {}),
            **({"other_links": other_link_timings} if other_link_timings else {}),
        },
        "crossref": crossref_data,
        "gemini_pdf": gemini_pdf.model_dump(),
        **({"gemini_page": page_supplementary.model_dump()} if page_supplementary else {}),
        **({"gemini_other_links": other_link_supplementary.model_dump()} if other_link_supplementary else {}),
        "final": final,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved to {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="Run LLM extraction for eval manifest")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS.keys()),
                        help=f"Gemini model (default: {DEFAULT_MODEL})")
    parser.add_argument("--force", action="store_true", help="Re-run even if output exists")
    parser.add_argument("--only", nargs="+", metavar="DOI_OR_NAME",
                        help="Only run entries whose DOI or PDF filename contains any of these "
                             "substrings (case-insensitive), e.g. --only Dobson Kerr")
    args = parser.parse_args()

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    if args.only:
        needles = [n.lower() for n in args.only]
        manifest = [
            e for e in manifest
            if any(n in e["doi"].lower() or n in e["pdf"].lower() for n in needles)
        ]
        if not manifest:
            print(f"[ERROR] No manifest entries matched --only {args.only}")
            return

    has_urls = sum(1 for e in manifest if e.get("url"))
    print(f"Running extraction for {len(manifest)} papers  |  model={args.model}  |  page scraping={has_urls}/{len(manifest)}")

    for i, entry in enumerate(manifest, 1):
        print(f"\n[{i}/{len(manifest)}]")
        await run_paper(entry, args.model, args.force)

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
