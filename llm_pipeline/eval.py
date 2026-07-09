"""
Eval script: compare LLM extraction outputs against GT.
Requires output JSONs to already exist (run run_batch.py first).

Usage (from science-portal-mailing/):
    python llm_pipeline/eval.py
    python llm_pipeline/eval.py --save eval_results.json
"""

import argparse
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
GT_PATH = HERE / "GT" / "200_science_portal.publications.json"
MANIFEST_PATH = HERE / "eval_manifest.json"


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")

    # Normalize http -> https
    url = re.sub(r"^http://", "https://", url)

    url = url.lower()

    # Strip query strings (removes signed CDN tokens like ?Expires=...&Signature=...)
    url = url.split("?")[0].rstrip("/")

    # Canonicalize www prefix for code hosting platforms
    for host in ("github.com", "gitlab.com", "bitbucket.org"):
        url = url.replace(f"https://www.{host}/", f"https://{host}/")

    # Canonicalize ClinicalTrials.gov: extract accession and rebuild canonical URL
    ct_match = re.search(r"(nct\d+)", url)
    if "clinicaltrials.gov" in url and ct_match:
        url = f"https://clinicaltrials.gov/study/{ct_match.group(1)}"

    return url


# ---------------------------------------------------------------------------
# Flattening
# ---------------------------------------------------------------------------

def is_article_pdf(url: str, doi: str) -> bool:
    """Return True if the URL is the article's own PDF rather than a supplementary file."""
    url_lower = url.lower()
    # Common article PDF path patterns used by publishers
    if any(p in url_lower for p in ("/article-pdf/", "/article_pdf/")):
        return True
    # Springer-style: URL filename is the DOI suffix (e.g. .../s13073-025-01583-w.pdf)
    doi_suffix = doi.split("/")[-1].lower()
    if url_lower.endswith(f"{doi_suffix}.pdf"):
        return True
    return False


def flatten_gt(supp: dict, doi: str = "") -> dict:
    """GT supplementary: {cat: {subcat: [url_str]}} → {cat.subcat: {urls}}
    Filters article PDFs out of miscellaneous.pdf since the LLM is instructed not to include them.
    """
    result = {}
    for cat, val in supp.items():
        if not isinstance(val, dict):
            continue
        for subcat, urls in val.items():
            if isinstance(urls, list) and urls:
                filtered = [
                    u for u in urls
                    if u and not (cat == "miscellaneous" and subcat == "pdf" and is_article_pdf(u, doi))
                ]
                norm = {normalize_url(u) for u in filtered}
                if norm:
                    result[f"{cat}.{subcat}"] = norm
    return result


def flatten_llm(supp: dict) -> dict:
    """LLM supplementary: {cat: {subcat: [{url, ...}]}} → {cat.subcat: {urls}}
    Skips list-type top-level categories (reagents, animalModels, biobanks).
    """
    result = {}
    for cat, val in supp.items():
        if not isinstance(val, dict):
            continue
        for subcat, resources in val.items():
            if isinstance(resources, list) and resources:
                urls = {normalize_url(r["url"]) for r in resources
                        if isinstance(r, dict) and r.get("url")}
                if urls:
                    result[f"{cat}.{subcat}"] = urls
    return result


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def metrics(gt_urls: set, llm_urls: set) -> dict:
    tp = len(gt_urls & llm_urls)
    fp = len(llm_urls - gt_urls)
    fn = len(gt_urls - llm_urls)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


# ---------------------------------------------------------------------------
# Per-paper eval
# ---------------------------------------------------------------------------

def eval_paper(gt_record: dict, output: dict) -> dict:
    gt_flat = flatten_gt(gt_record.get("supplementary") or {}, doi=gt_record.get("doi", ""))
    llm_flat = flatten_llm(output["final"]["supplementary"])

    all_cats = sorted(set(gt_flat) | set(llm_flat))

    per_cat = {}
    for cat in all_cats:
        gt_urls = gt_flat.get(cat, set())
        llm_urls = llm_flat.get(cat, set())
        per_cat[cat] = {
            "gt_count": len(gt_urls),
            "llm_count": len(llm_urls),
            "gt_urls": sorted(gt_urls),
            "llm_urls": sorted(llm_urls),
            **metrics(gt_urls, llm_urls),
        }

    # Aggregate over categories that have GT entries
    gt_cats = [v for v in per_cat.values() if v["gt_count"] > 0]
    if gt_cats:
        agg_p = sum(v["precision"] for v in gt_cats) / len(gt_cats)
        agg_r = sum(v["recall"] for v in gt_cats) / len(gt_cats)
        agg_f = sum(v["f1"] for v in gt_cats) / len(gt_cats)
    else:
        agg_p = agg_r = agg_f = 0.0

    fp_only = [c for c, v in per_cat.items() if v["gt_count"] == 0 and v["llm_count"] > 0]

    # Fields the LLM captured that GT does not have (across ALL categories,
    # not just fp_only ones — e.g. an extra url within a category GT partially covers)
    extra_fields = [
        {"category": cat, "url": u}
        for cat, v in sorted(per_cat.items())
        for u in v["llm_urls"]
        if u not in set(v["gt_urls"])
    ]

    return {
        "doi": gt_record["doi"],
        "name": gt_record.get("name", ""),
        "model": output.get("model", ""),
        "per_category": per_cat,
        "aggregate": {
            "precision": round(agg_p, 3),
            "recall": round(agg_r, 3),
            "f1": round(agg_f, 3),
            "gt_category_count": len(gt_cats),
            "fp_only_categories": fp_only,
        },
        "llm_extra_fields": {
            "count": len(extra_fields),
            "fields": extra_fields,
        },
    }


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def print_results(results: list) -> None:
    W = 72

    print("\n" + "=" * W)
    print("EVAL RESULTS")
    print("=" * W)

    for i, r in enumerate(results, 1):
        agg = r["aggregate"]
        per_cat = r["per_category"]

        print(f"\nPaper {i}/{len(results)}: {r['name'][:55]}")
        print(f"  DOI: {r['doi']}  |  Model: {r['model']}")
        print("-" * W)

        gt_cats = {c: v for c, v in per_cat.items() if v["gt_count"] > 0}

        if gt_cats:
            print(f"  {'Category':<33} {'GT':>3} {'LLM':>3} {'TP':>3} {'FP':>3} {'FN':>3}  "
                  f"{'Prec':>6}  {'Rec':>6}  {'F1':>6}")
            print("  " + "-" * 67)
            for cat, m in sorted(gt_cats.items()):
                print(f"  {cat:<33} {m['gt_count']:>3} {m['llm_count']:>3} "
                      f"{m['tp']:>3} {m['fp']:>3} {m['fn']:>3}  "
                      f"{m['precision']:>6.3f}  {m['recall']:>6.3f}  {m['f1']:>6.3f}")
        else:
            print("  (no supplementary resources in GT for this paper)")

        extra = r["llm_extra_fields"]
        if extra["count"]:
            print(f"\n  LLM captured, GT missed ({extra['count']}):")
            for f in extra["fields"]:
                print(f"    [{f['category']}] {f['url']}")

        print(f"\n  Aggregate ({agg['gt_category_count']} GT categories):  "
              f"Precision={agg['precision']:.3f}  "
              f"Recall={agg['recall']:.3f}  "
              f"F1={agg['f1']:.3f}")

    if not results:
        print("  No results to display.")
        return

    print("\n" + "=" * W)
    print("OVERALL SUMMARY")
    print("=" * W)
    print(f"  {'Paper':<35} {'Prec':>6}  {'Rec':>6}  {'F1':>6}")
    print("  " + "-" * 55)
    for r in results:
        agg = r["aggregate"]
        print(f"  {r['name'][:33]:<35} {agg['precision']:>6.3f}  "
              f"{agg['recall']:>6.3f}  {agg['f1']:>6.3f}")
    print("  " + "-" * 55)
    macro_p = sum(r["aggregate"]["precision"] for r in results) / len(results)
    macro_r = sum(r["aggregate"]["recall"] for r in results) / len(results)
    macro_f = sum(r["aggregate"]["f1"] for r in results) / len(results)
    print(f"  {'Macro average':<35} {macro_p:>6.3f}  {macro_r:>6.3f}  {macro_f:>6.3f}")
    print("=" * W)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM extraction against GT")
    parser.add_argument("--save", default=None, metavar="PATH",
                        help="Save full results to a JSON file")
    args = parser.parse_args()

    with open(GT_PATH) as f:
        gt_by_doi = {d["doi"]: d for d in json.load(f)}

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    results = []
    for entry in manifest:
        doi = entry["doi"]
        output_path = ROOT / entry["output"]

        if not output_path.exists():
            print(f"[SKIP] No output JSON for {doi} — run run_batch.py first")
            continue

        gt_record = gt_by_doi.get(doi)
        if not gt_record:
            print(f"[SKIP] DOI {doi} not found in GT")
            continue

        with open(output_path) as f:
            output = json.load(f)

        results.append(eval_paper(gt_record, output))

    print_results(results)

    if args.save and results:
        save_path = pathlib.Path(args.save)
        with open(save_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nFull results saved to {save_path}")


if __name__ == "__main__":
    main()
