"""
Test script to compare Crossref API output vs Gemini PDF extraction for a given paper.

Usage:
    python llm_pipeline/test_extraction.py --pdf /path/to/paper.pdf --doi 10.1038/... --url https://publisher.com/article/...
    python llm_pipeline/test_extraction.py --pdf /path/to/paper.pdf --doi 10.1038/... --url https://... --model gemini-3.1-flash-lite
    python llm_pipeline/test_extraction.py --pdf /path/to/paper.pdf --doi 10.1038/...   # --url is optional
"""

import argparse
import asyncio
import json
import os
import pathlib
import requests
import time
from typing import List
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv(pathlib.Path(__file__).parent / ".env")

DEFAULT_MODEL = "gemini-3.1-pro-preview"

MODELS = {
    "gemini-3.1-pro-preview": {"model_id": "gemini-3.1-pro-preview", 
                               "temperature": 0.0, 
                               "timeout": 180},
    
    "gemini-3-flash-preview":  {"model_id": "gemini-3-flash-preview",
                                "temperature": 0.0,
                                "timeout": 300},
    
    "gemini-3.1-flash-lite":  {"model_id": "gemini-3.1-flash-lite",  
                                "temperature": 0.0, 
                                "timeout": 180},
}

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_model_config(model_name: str) -> dict:
    if model_name not in MODELS:
        raise ValueError(f"Model '{model_name}' not found. Available: {list(MODELS.keys())}")
    return MODELS[model_name]


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class Resource(BaseModel):
    url: str = ""
    original: bool = True
    description: str = ""

class NonURLResource(BaseModel):
    name: str = ""
    identifier: str = ""
    original: bool = True
    description: str = ""

class CodeLinks(BaseModel):
    github: List[Resource] = []
    gitlab: List[Resource] = []
    bitbucket: List[Resource] = []

class DataLinks(BaseModel):
    geo: List[Resource] = []
    dbGap: List[Resource] = []
    kaggle: List[Resource] = []
    dryad: List[Resource] = []
    empiar: List[Resource] = []
    gigaDb: List[Resource] = []
    zenodo: List[Resource] = []
    ega: List[Resource] = []
    xlsx: List[Resource] = []
    csv: List[Resource] = []
    proteinDataBank: List[Resource] = []
    dataverse: List[Resource] = []
    openScienceFramework: List[Resource] = []
    finngenGitbook: List[Resource] = []
    gtexPortal: List[Resource] = []
    ebiAcUk: List[Resource] = []
    mendeley: List[Resource] = []
    R: List[Resource] = []
    xls: List[Resource] = []

class ContainerLinks(BaseModel):
    codeOcean: List[Resource] = []
    colab: List[Resource] = []

class ResultLinks(BaseModel):
    gsea: List[Resource] = []
    figshare: List[Resource] = []

class TrialLinks(BaseModel):
    clinicalTrial: List[Resource] = []
    euCTR: List[Resource] = []
    vivli: List[Resource] = []
    yoda: List[Resource] = []

class CellLineLinks(BaseModel):
    cellosaurus: List[Resource] = []

class PlasmidLinks(BaseModel):
    addgene: List[Resource] = []
    dnasu: List[Resource] = []
    deepomics: List[Resource] = []

class ProtocolLinks(BaseModel):
    protocolsIO: List[Resource] = []
    bioProtocol: List[Resource] = []
    benchling: List[Resource] = []
    labArchives: List[Resource] = []

class PackageLinks(BaseModel):
    bioconductor: List[Resource] = []
    pypi: List[Resource] = []
    CRAN: List[Resource] = []

class MiscLinks(BaseModel):
    IEEE: List[Resource] = []
    pdf: List[Resource] = []
    docx: List[Resource] = []
    zip: List[Resource] = []
    ppt: List[Resource] = []

class Supplementary(BaseModel):
    code: CodeLinks = Field(default_factory=CodeLinks)
    data: DataLinks = Field(default_factory=DataLinks)
    containers: ContainerLinks = Field(default_factory=ContainerLinks)
    results: ResultLinks = Field(default_factory=ResultLinks)
    trials: TrialLinks = Field(default_factory=TrialLinks)
    celllines: CellLineLinks = Field(default_factory=CellLineLinks)
    plasmids: PlasmidLinks = Field(default_factory=PlasmidLinks)
    protocols: ProtocolLinks = Field(default_factory=ProtocolLinks)
    packages: PackageLinks = Field(default_factory=PackageLinks)
    miscellaneous: MiscLinks = Field(default_factory=MiscLinks)
    reagents: List[NonURLResource] = []
    animalModels: List[NonURLResource] = []
    biobanks: List[NonURLResource] = []


class OtherLink(BaseModel):
    name: str = ""
    recommendedCategory: str = ""
    description: str = ""
    link: str = ""


class Pub(BaseModel):
    doi: str = ""
    date: str = ""
    name: str = ""
    journal: str = ""
    type: str = ""
    abstract: str = ""
    authors: str = ""
    affiliations: List[str] = []
    publisher: str = ""
    status: str = "published"
    supplementary: Supplementary = Field(default_factory=Supplementary)
    otherLinks: List[OtherLink] = []


# ---------------------------------------------------------------------------
# Crossref
# ---------------------------------------------------------------------------

def fetch_crossref(doi: str) -> dict:
    print(f"\n{'='*60}")
    print(f"CROSSREF API: {doi}")
    print(f"{'='*60}")

    start = time.time()
    r = requests.get(
        f"https://api.crossref.org/works/{doi}",
        headers={"User-Agent": "Python-requests", "Mailto": "support@pmscience.ca"},
        timeout=60,
    )

    if r.status_code != 200:
        raise Exception(f"Crossref returned {r.status_code}")

    data = r.json()
    if data.get("status") != "ok":
        raise Exception(f"Crossref status not ok: {data}")

    msg = data["message"]
    elapsed = time.time() - start

    result = {
        "title": msg.get("title", [""])[0],
        "authors": [
            f"{a.get('family', '')}, {a.get('given', '')}"
            for a in msg.get("author", [])
        ],
        "affiliations": list({
            affil["name"]
            for a in msg.get("author", [])
            for affil in a.get("affiliation", [])
        }),
        "date": msg.get("created", {}).get("date-time", "")[:10],
        "journal": (msg.get("container-title") or msg.get("institution", [{}]))[0] if (msg.get("container-title") or msg.get("institution")) else "",
        "type": msg.get("type", ""),
        "abstract": msg.get("abstract", ""),
        "citations": msg.get("is-referenced-by-count", 0),
        "publisher": msg.get("publisher", ""),
        "doi": doi,
    }

    # print(json.dumps(result, indent=2))
    print(f"Completed in {elapsed:.1f}s")
    return result


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """
You are an expert in extracting structured metadata from scientific publications.

Your task: Read the full PDF and fill out the schema below completely and accurately.

General rules:
- Extract all publication metadata (title, authors, journal, abstract, date, publisher, DOI).
- Authors should be formatted as "LastName, FirstName" separated by semicolons.
- For supplementary resources, only include resources explicitly mentioned in the paper (URLs, accession numbers, or named reagents/models).
- Do not generate or guess URLs — only include ones explicitly present in the text.
- Do not include resources from the references section unless their URL or accession number is explicitly stated.
- Always output full URLs, not bare accession numbers. Resolve accessions using the canonical base URLs below.
- A link classified into one subcategory should not appear in another.
- If a resource does not fit any predefined subcategory, put it into otherLinks.

Resource originality (the `original` field):
- Set `original: true` if the authors generated or deposited this resource specifically for this paper (e.g., sequencing data they produced, code they wrote, a protocol they developed).
- Set `original: false` if the resource was created by others and the authors merely reused it (e.g., a public reference genome, a previously published dataset, an external tool repository not authored by this paper's team).
- When uncertain, default to `true`.

Resource description (the `description` field):
- Write a short phrase (5–15 words) describing what the resource contains or is used for.
- Example: "RNA-seq count matrices for all tumor samples", "Custom R scripts for survival analysis".
- Leave empty string if nothing informative can be said beyond the URL.

Non-URL resources — reagents, animal models, and biobanks:
- These do not have standard URLs; use the NonURLResource schema: {name, identifier, original, description}.
- `name`: the common name of the reagent, strain, or cohort.
- `identifier`: a catalog number, RRID, strain ID, IRB number, or other formal identifier if stated; otherwise empty string.
- `original`: true if created/established by the authors for this paper; false if purchased, licensed, or borrowed from an existing source.
- reagents: antibodies (include clone, catalog #, vendor if stated), CRISPR reagents (guides, Cas9 constructs), primers, chemicals with catalog IDs.
- animalModels: mouse strains (include JAX stock number or MGI ID if stated), PDX models, organoid lines, transgenic lines.
- biobanks: named patient cohorts, biobank collections, or IRB-identified sample sets used in the study.

Subcategory mapping (place each URL in the matching subcategory field):
  code.github            → github.com URLs
  code.gitlab            → gitlab.com URLs
  code.bitbucket         → bitbucket.org URLs
  data.geo               → ncbi.nlm.nih.gov/geo — resolve GSE accessions to https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSExxxxxx
  data.dbGap             → ncbi.nlm.nih.gov/gap — resolve phs accessions to https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phsxxxxxx
  data.kaggle            → kaggle.com
  data.dryad             → datadryad.org
  data.empiar            → ebi.ac.uk/empiar
  data.gigaDb            → gigadb.org
  data.zenodo            → zenodo.org
  data.ega               → ega-archive.org — resolve EGAS/EGAD accessions to https://ega-archive.org/studies/EGASxxxxxx or https://ega-archive.org/datasets/EGADxxxxxx
  data.xlsx              → direct .xlsx file URLs
  data.csv               → direct .csv file URLs
  data.xls               → direct .xls file URLs
  data.proteinDataBank   → rcsb.org or wwpdb.org
  data.dataverse         → dataverse URLs
  data.openScienceFramework → osf.io
  data.finngenGitbook    → finngen URLs
  data.gtexPortal        → gtexportal.org
  data.ebiAcUk           → ebi.ac.uk (excluding empiar)
  data.mendeley          → mendeley.com/catalogue
  data.R                 → direct .rds file URLs
  containers.codeOcean   → codeocean.com
  containers.colab       → colab.research.google.com
  results.gsea           → gsea-msigdb.org
  results.figshare       → figshare.com
  trials.clinicalTrial   → clinicaltrials.gov
  trials.euCTR           → clinicaltrialsregister.eu
  trials.vivli           → vivli.org
  trials.yoda            → yoda.yale.edu
  celllines.cellosaurus  → cellosaurus.org — resolve CVCL_* accessions to https://www.cellosaurus.org/CVCL_xxxx
  plasmids.addgene       → addgene.org
  plasmids.dnasu         → dnasu.org
  plasmids.deepomics     → plasmid.deepomics.org
  protocols.protocolsIO  → protocols.io
  protocols.bioProtocol  → bio-protocol.org
  protocols.benchling    → benchling.com
  protocols.labArchives  → mynotebook.labarchives.com
  packages.bioconductor  → bioconductor.org
  packages.pypi          → pypi.org
  packages.CRAN          → cran.r-project.org
  miscellaneous.IEEE     → ieee.org URLs
  miscellaneous.pdf      → direct .pdf file URLs
  miscellaneous.docx     → direct .docx file URLs
  miscellaneous.zip      → direct .zip file URLs
  miscellaneous.ppt      → direct .ppt file URLs

Respond with valid JSON strictly matching the provided schema.
"""

CLASSIFICATION_PROMPT = """
You are classifying URLs extracted from a scientific publication's webpage.

Below is a list of links in "label: url" format. Classify each URL into the correct subcategory field.

Rules:
- Only include URLs that belong to a supplementary resource category (data, code, containers, etc.).
- Ignore navigation links, author profiles, journal homepages, social media, citation counts, and reference links.
- Output full URLs exactly as given — do not modify them.
- A URL classified into one subcategory should not appear in another.
- For each resource, set `original: true` (these are publisher-hosted supplementary files deposited by the authors).
- Leave `description` as empty string — descriptions will be filled from the PDF extraction.

Subcategory mapping:
  code.github            → github.com URLs
  code.gitlab            → gitlab.com URLs
  code.bitbucket         → bitbucket.org URLs
  data.geo               → ncbi.nlm.nih.gov/geo
  data.dbGap             → ncbi.nlm.nih.gov/gap
  data.kaggle            → kaggle.com
  data.dryad             → datadryad.org
  data.empiar            → ebi.ac.uk/empiar
  data.gigaDb            → gigadb.org
  data.zenodo            → zenodo.org
  data.ega               → ega-archive.org
  data.xlsx              → .xlsx file URLs
  data.csv               → .csv file URLs
  data.xls               → .xls file URLs
  data.proteinDataBank   → rcsb.org or wwpdb.org
  data.dataverse         → dataverse URLs
  data.openScienceFramework → osf.io
  data.finngenGitbook    → finngen URLs
  data.gtexPortal        → gtexportal.org
  data.ebiAcUk           → ebi.ac.uk (excluding empiar)
  data.mendeley          → mendeley.com/catalogue
  data.R                 → .rds file URLs
  containers.codeOcean   → codeocean.com
  containers.colab       → colab.research.google.com
  results.gsea           → gsea-msigdb.org
  results.figshare       → figshare.com
  trials.clinicalTrial   → clinicaltrials.gov
  trials.euCTR           → clinicaltrialsregister.eu
  trials.vivli           → vivli.org
  trials.yoda            → yoda.yale.edu
  celllines.cellosaurus  → cellosaurus.org
  plasmids.addgene       → addgene.org
  plasmids.dnasu         → dnasu.org
  plasmids.deepomics     → plasmid.deepomics.org
  protocols.protocolsIO  → protocols.io
  protocols.bioProtocol  → bio-protocol.org
  protocols.benchling    → benchling.com
  protocols.labArchives  → mynotebook.labarchives.com
  packages.bioconductor  → bioconductor.org
  packages.pypi          → pypi.org
  packages.CRAN          → cran.r-project.org
  miscellaneous.IEEE     → ieee.org URLs
  miscellaneous.pdf      → .pdf file URLs
  miscellaneous.docx     → .docx file URLs
  miscellaneous.zip      → .zip file URLs
  miscellaneous.ppt      → .ppt file URLs

Respond with valid JSON strictly matching the provided schema.
"""


def fetch_gemini(pdf_path: pathlib.Path, model_name: str) -> Pub:
    model_config = load_model_config(model_name)
    model_id = model_config["model_id"]
    temperature = model_config["temperature"]
    timeout = model_config["timeout"]

    print(f"\n{'='*60}")
    print(f"GEMINI EXTRACTION: {pdf_path.name}")
    print(f"Model: {model_id} | Temperature: {temperature} | Timeout: {timeout}s")
    print(f"{'='*60}")

    api_key = os.getenv("GEMINI_API_KEY")

    # No timeout override for upload — let SDK use its default for the file upload path
    upload_client = genai.Client(api_key=api_key)
    # HttpOptions timeout is in milliseconds
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout * 1000),
    )

    # Upload PDF via Files API first — avoids inline write timeout on large PDFs
    print("Uploading PDF...")
    t_upload_start = time.time()
    pdf_file = upload_client.files.upload(
        file=pdf_path,
        config=types.UploadFileConfig(mime_type="application/pdf"),
    )
    print(f"Uploaded: {pdf_file.name}")

    # Wait for Gemini to finish processing the file
    while pdf_file.state == types.FileState.PROCESSING:
        print("Waiting for file processing...")
        time.sleep(2)
        pdf_file = upload_client.files.get(name=pdf_file.name)

    if pdf_file.state == types.FileState.FAILED:
        raise Exception("PDF processing failed on Gemini servers")

    t_upload_elapsed = time.time() - t_upload_start
    print(f"Upload + processing: {t_upload_elapsed:.1f}s")

    print("Running inference...")
    t_inference_start = time.time()
    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Part.from_uri(file_uri=pdf_file.uri, mime_type="application/pdf"),
            EXTRACTION_PROMPT,
        ],
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=Pub,
        ),
    )
    t_inference_elapsed = time.time() - t_inference_start
    print(f"Inference: {t_inference_elapsed:.1f}s")
    print(f"Total Gemini: {t_upload_elapsed + t_inference_elapsed:.1f}s")

    # Clean up uploaded file
    try:
        upload_client.files.delete(name=pdf_file.name)
    except Exception:
        pass

    pub = response.parsed
    # print(json.dumps(pub.model_dump(), indent=2))
    return pub, {
        "upload_s": round(t_upload_elapsed, 1),
        "inference_s": round(t_inference_elapsed, 1),
        "total_s": round(t_upload_elapsed + t_inference_elapsed, 1),
    }


# ---------------------------------------------------------------------------
# Page link extraction + classification
# ---------------------------------------------------------------------------

async def fetch_page_links(url: str) -> str:
    print(f"\n{'='*60}")
    print(f"PAGE LINK EXTRACTION: {url}")
    print(f"{'='*60}")

    start = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",   # use system Chrome — better Cloudflare handling
            headless=False,
        )
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)   # let Cloudflare JS challenge resolve
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    lines = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        if not href or not text:
            continue
        if href.startswith(("mailto:", "#", "javascript:")):
            continue
        if href in seen:
            continue
        seen.add(href)
        lines.append(f"{text}: {href}")

    elapsed = round(time.time() - start, 1)
    print(f"Extracted {len(lines)} links in {elapsed}s")
    return "\n".join(lines), elapsed


def classify_page_links(links_text: str, model_name: str) -> tuple:
    model_config = load_model_config(model_name)
    model_id = model_config["model_id"]
    temperature = model_config["temperature"]
    timeout = model_config["timeout"]

    print(f"\n{'='*60}")
    print(f"GEMINI PAGE CLASSIFICATION")
    print(f"Model: {model_id}")
    print(f"{'='*60}")

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout * 1000),
    )

    start = time.time()
    response = client.models.generate_content(
        model=model_id,
        contents=f"{CLASSIFICATION_PROMPT}\n\n---\n\n{links_text}",
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=Supplementary,
        ),
    )
    elapsed = time.time() - start
    print(f"Completed in {elapsed:.1f}s")

    return response.parsed, {"page_classify_s": round(elapsed, 1)}


def merge_supplementary(a: Supplementary, b: Supplementary) -> Supplementary:
    a_dict = a.model_dump()
    b_dict = b.model_dump()
    merged = {}
    for category, a_val in a_dict.items():
        if isinstance(a_val, list):
            # Top-level List[NonURLResource] — deduplicate by identifier, fall back to name
            b_val = b_dict[category]
            seen = {r["identifier"] or r["name"] for r in a_val if r["identifier"] or r["name"]}
            extras = [r for r in b_val if (r["identifier"] or r["name"]) not in seen]
            merged[category] = a_val + extras
        else:
            # Category is a dict of subcategories, each List[Resource]
            merged[category] = {}
            for subcat, a_resources in a_val.items():
                b_resources = b_dict[category][subcat]
                seen_urls = {r["url"] for r in a_resources if r["url"]}
                extras = [r for r in b_resources if r["url"] not in seen_urls]
                merged[category][subcat] = a_resources + extras
    return Supplementary(**merged)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Compare Crossref vs Gemini PDF extraction")
    parser.add_argument("--pdf", required=True, help="Path to the paper PDF")
    parser.add_argument("--doi", required=True, help="DOI of the paper (e.g. 10.1038/s41586-021-03819-2)")
    parser.add_argument("--url", default=None, help="Publisher page URL for supplementary link extraction (optional)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL}). Available: {list(MODELS.keys())}")
    parser.add_argument("--output", default="Results/output.json", help="Path to save output JSON")
    args = parser.parse_args()

    pdf_path = pathlib.Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Step 1: Crossref
    t_crossref_start = time.time()
    crossref_data = fetch_crossref(args.doi)
    crossref_elapsed = round(time.time() - t_crossref_start, 1)

    # Step 2: Gemini PDF extraction
    gemini_pdf, pdf_timing = fetch_gemini(pdf_path, args.model)

    # Step 3: Page link extraction + classification (optional)
    page_supplementary = None
    page_timing = {}
    if args.url:
        links_text, page_scrape_s = await fetch_page_links(args.url)
        page_supplementary, page_timing = classify_page_links(links_text, args.model)
        page_timing["page_scrape_s"] = page_scrape_s

    # Step 4: Merge supplementary
    if page_supplementary:
        merged_supplementary = merge_supplementary(gemini_pdf.supplementary, page_supplementary)
    else:
        merged_supplementary = gemini_pdf.supplementary

    # Step 5: Assemble final — override date/type/publisher with Crossref
    final = gemini_pdf.model_dump()
    final["date"] = crossref_data["date"]
    final["type"] = crossref_data["type"]
    final["publisher"] = crossref_data["publisher"]
    final["citations"] = crossref_data["citations"]
    final["supplementary"] = merged_supplementary.model_dump()

    print(f"\n{'='*60}")
    print(f"TIMING SUMMARY")
    print(f"{'='*60}")
    print(f"Crossref API:          {crossref_elapsed}s")
    print(f"Gemini PDF upload:     {pdf_timing['upload_s']}s")
    print(f"Gemini PDF inference:  {pdf_timing['inference_s']}s")
    print(f"Gemini PDF total:      {pdf_timing['total_s']}s")
    if page_timing:
        print(f"Page scrape (Playwright): {page_timing['page_scrape_s']}s")
        print(f"Gemini page classify:     {page_timing['page_classify_s']}s")

    output = {
        "doi": args.doi,
        "pdf": str(pdf_path),
        "url": args.url,
        "model": args.model,
        "timing": {
            "crossref_s": crossref_elapsed,
            "gemini_pdf_upload_s": pdf_timing["upload_s"],
            "gemini_pdf_inference_s": pdf_timing["inference_s"],
            "gemini_pdf_total_s": pdf_timing["total_s"],
            **({"page_scrape_s": page_timing["page_scrape_s"], "gemini_page_s": page_timing["page_classify_s"]} if page_timing else {}),
        },
        "crossref": crossref_data,
        "gemini_pdf": gemini_pdf.model_dump(),
        **({"gemini_page": page_supplementary.model_dump()} if page_supplementary else {}),
        "final": final,
    }

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Saved to {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
