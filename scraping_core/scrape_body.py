from dotenv import load_dotenv
import re

# Accession Patterns
GSE_MENTION_PATTERN = re.compile(r"\bGSE\s?-?\s?(\d{4,6})\b", re.IGNORECASE)
NCT_MENTION_PATTERN = re.compile(r"\bNCT[\s-]?(\d{8})\b", re.IGNORECASE)
DB_GAP_PATTERN = re.compile(r"\b(phs\d{6}\.v\d+\.p\d+)\b", re.IGNORECASE)
EGA_PATTERN = re.compile(r"\b(EGAS\d+)\b", re.IGNORECASE)

# DOI Patterns
DOI_PATTERNS = {
    "zenodo": (re.compile(r"10\.5281/zenodo\.(\d+)", re.IGNORECASE), lambda m: f"https://doi.org/10.5281/zenodo.{m.group(1)}"),
    "dryad": (re.compile(r"10\.5061/dryad\.(\w+)", re.IGNORECASE), lambda m: f"https://doi.org/10.5061/dryad.{m.group(1)}"),
    "figshare": (re.compile(r"10\.6084/m9\.figshare\.(\d+)", re.IGNORECASE), lambda m: f"https://figshare.com/articles/online_resource/{m.group(1)}"),
    "codeOcean": (re.compile(r"10\.24433/CO\.(\d+)", re.IGNORECASE), lambda m: f"https://doi.org/10.24433/CO.{m.group(1)}.v1"),
    "dataverse": (re.compile(r"10\.7910/DVN/(\w+)", re.IGNORECASE), lambda m: f"https://doi.org/10.7910/DVN/{m.group(1)}"),
    "empiar": (re.compile(r"10\.6019/EMPIAR-(\d+)", re.IGNORECASE), lambda m: f"https://www.ebi.ac.uk/empiar/EMPIAR-{m.group(1)}"),
    "gigaDb": (re.compile(r"10\.5524/(\w+)", re.IGNORECASE), lambda m: f"https://gigadb.org/dataset/{m.group(1)}"),
    "mendeley": (re.compile(r"10\.17632/([\w]+)", re.IGNORECASE), lambda m: f"https://data.mendeley.com/datasets/{m.group(1)}/1"),
    "protocolsIO": (re.compile(r"10\.17504/protocols\.io\.(\w+)", re.IGNORECASE), lambda m: f"https://www.protocols.io/view/{m.group(1)}"),
}

load_dotenv()

def scrape_body(body_text: str):

    links = set()
    body_text = str(body_text)

    # GEO
    for gse_id in GSE_MENTION_PATTERN.findall(body_text):
        links.add(f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE{gse_id}")

    # ClinicalTrials
    for nct_id in NCT_MENTION_PATTERN.findall(body_text):
        links.add(f"https://www.clinicaltrials.gov/ct2/show/NCT{nct_id}")

    # dbGaP
    for phs_id in DB_GAP_PATTERN.findall(body_text):
        links.add(f"https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={phs_id}")

    # EGA
    for ega_id in EGA_PATTERN.findall(body_text):
        links.add(f"https://ega-archive.org/studies/{ega_id}")

    # DOIs
    for platform, (pattern, url_func) in DOI_PATTERNS.items():
        for match in pattern.finditer(body_text):
            links.add(url_func(match))


    print(f"Extracted {len(links)} links from text body")
    
    return links