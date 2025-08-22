import re
from urllib.parse import urlparse, parse_qs, urlunparse
from scraping_core.write_to_json import write_to_json

SUPPLEMENTARY = {
    "code": ["github", "gitlab", "bitbucket"],
    "data": [
        "geo", "dbGap", "kaggle", "dryad", "empiar", "gigaDb", "zenodo", "ega", "xlsx", "csv",
        "proteinDataBank", "dataverse", "openScienceFramework", "finngenGitbook", "gtexPortal",
        "ebiAcUk", "mendeley", "R", "cellosaurus", "xls",
    ],
    "containers": ["codeOcean", "colab"],
    "results": ["gsea", "figshare"],
    "trials": ["clinicalTrial", "euCTR", "vivli", "yoda"],
    "protocols": ["protocolsIO", "bioProtocol", "benchling", "labArchives"],
    "packages": ["bioconductor", "pypi", "CRAN"],
    "miscellaneous": ["IEEE", "pdf", "docx", "zip","ppt", "jpg", "png"],
}

SUPPLEMENTARY_PATTERNS = {
    "github": re.compile(r"^https?://(?:www\.)?github\.com/[\w\-]+/[\w\-]+(?:/[^/?#]+)?/?$", re.IGNORECASE),
    "gitlab": re.compile(r"https?://(?:www\.)?gitlab\.com/[\w\-]+/[\w\-]+(?:/.*)?", re.IGNORECASE),
    "geo": re.compile(r"https?://(?:www\.)?ncbi\.nlm\.nih\.gov/geo/query/acc\.cgi\?acc=GSE\d+|ftp://ftp\.ncbi\.nlm\.nih\.gov/geo/.+|https?://identifiers\.org/GEO:GSE\d+", re.IGNORECASE),
    "dbGap": re.compile(r"https?://(?:www\.)?ncbi\.nlm\.nih\.gov/projects/gap/cgi-bin/study\.cgi\?study_id=phs\d+(?:\.v\d+(?:\.p\d+)?)?", re.IGNORECASE),
    "kaggle": re.compile(r"https?://[^ ]*kaggle[^ ]*", re.IGNORECASE),
    "dryad": re.compile(r"https?://[^ ]*datadryad\.org/(?!($|stash/?$))[^ ]+|https?://[^ ]*doi\.org/10\.5061/dryad\.[^ ]+", re.IGNORECASE),
    "empiar": re.compile(r"https?://(?:www\.)?ebi\.ac\.uk/empiar/EMPIAR-\d+", re.IGNORECASE),
    "gigaDb": re.compile(r"https?://(?:www\.)?gigadb\.org/dataset/\d+", re.IGNORECASE),
    "zenodo": re.compile(r"https?://(?:www\.)?(zenodo\.org|doi\.org/10\.5281/zenodo\.\d+)", re.IGNORECASE),
    "ega": re.compile(r"https?://(?:www\.)?ega-archive\.org/(studies|datasets)/[\w\-]+", re.IGNORECASE),
    "xlsx": re.compile(r"\.xlsx($|\?)", re.IGNORECASE),
    "csv": re.compile(r"\.csv($|\?)", re.IGNORECASE),
    "proteinDataBank": re.compile(r"https?://(?:www\.)?(rcsb|wwpdb)\.org/.+|https?://(?:www\.)?doi\.org/10\.2210/pdb\w+/pdb", re.IGNORECASE),
    "dataverse": re.compile(r"https?://(?:www\.)?(dataverse\..+?|doi\.org/10\.7910/DVN/[\w]+)", re.IGNORECASE),
    "openScienceFramework": re.compile(r"https?://(?:osf\.io/\w+|doi\.org/10\.17605/OSF\.IO/\w+)", re.IGNORECASE),
    "finngenGitbook": re.compile(r"https?://[^ \s]*finngen[^ \s]*", re.IGNORECASE),
    "gtexPortal": re.compile(r"https?://(?:www\.)?gtexportal\.org/.+|https?://gtexportal\.org/.+", re.IGNORECASE),
    "ebiAcUk": re.compile(r"https?://[^ ]*ebi\.ac\.uk[^ ]*|ftp://[^ ]*sra\.ebi\.ac\.uk[^ ]*|https?://[^ ]*ena\.embl[^ ]*", re.IGNORECASE),
    "mendeley": re.compile(r"https?://(?:www\.)?mendeley\.com/catalogue/[\w\-]+/?", re.IGNORECASE),
    "R": re.compile(r"\.rds($|\?)", re.IGNORECASE),
    "codeOcean": re.compile(
        r"https?://(?:www\.)?codeocean\.com/(algo\.html\?algorithmSlug=|capsule/)[\w\-/]+"
        r"|https?://(?:www\.)?doi\.org/10\.24433/CO\.\d+(?:\.v\d+)?", re.IGNORECASE
    ),
    "colab": re.compile(r"https?://(?:www\.)?colab\.research\.google\.com/github/.+\.ipynb", re.IGNORECASE),
    "gsea": re.compile(r"https?://(?:www\.)?gsea-msigdb\.org/gsea/msigdb/.+", re.IGNORECASE),
    "figshare": re.compile(r"https?://(?:www\.)?(figshare\.com|doi\.org/10\.6084/m9\.figshare\.\d+)", re.IGNORECASE),
    "clinicalTrial": re.compile(r"https?://(?:www\.)?clinicaltrials\.gov/ct2/show/NCT\d+/?(?:\?.*)?", re.IGNORECASE),
    "euCTR": re.compile(r"https?://(?:www\.)?clinicaltrialsregister\.eu/ctr-search/trial/\d{4}-\d{6}-\d{2}/[A-Z]{2}", re.IGNORECASE),
    "vivli": re.compile(r"https?://[^ ]*vivli[^ ]*", re.IGNORECASE),
    "yoda": re.compile(r"https?://(?:www\.)?yoda\.yale\.edu/.+", re.IGNORECASE),
    "bioconductor": re.compile(r"https?://(?:www\.)?bioconductor\.org/packages/(?:release|[\d\.]+)/bioc/html/.+|https?://(?:www\.)?bioconductor\.org/packages/[\w\-]+", re.IGNORECASE),
    "pypi": re.compile(r"https?://(?:www\.)?pypi\.org/project/.+|https?://pypi\.python\.org/pypi/.+", re.IGNORECASE),
    "CRAN": re.compile(r"https?://(?:cran\.(r-project|rstudio)\.org|ggplot2\.tidyverse\.org)/web/packages/.+", re.IGNORECASE),
    # "IEEE": re.compile(r"https?://(?:www\.)?ieeexplore\.ieee\.org/document/\d+", re.IGNORECASE),
    "IEEE": re.compile(r"https?://[^ ]*ieee[^ ]*", re.IGNORECASE),
    "pdf": re.compile(r"\.pdf($|\?)", re.IGNORECASE),
    "docx": re.compile(r"\.docx($|\?)", re.IGNORECASE),
    "zip": re.compile(r"\.zip($|\?)", re.IGNORECASE),
    "protocolsIO": re.compile(r"https?://(?:www\.)?protocols\.io/view/.+", re.IGNORECASE),
    "bioProtocol": re.compile(r"https?://(?:www\.)?bio-protocol\.org/(en/bpdetail|exchange/protocoldetail)\?id=\d+.*"
        r"|https?://en-cdn\.bio-protocol\.org/pdf/bio-protocol\d+\.pdf.*"
        r"|https?://doi\.org/10\.21769/BioProtoc\.\d+",
        re.IGNORECASE
    ),
    "benchling": re.compile(r"https?://(?:www\.)?benchling\.com/(protocols|s)/[^\s]+", re.IGNORECASE),
    "labArchives": re.compile(r"https?://(?:www\.)?mynotebook\.labarchives\.com/.+", re.IGNORECASE),
    "cellosaurus": re.compile(r"https?://(?:(?:www\.)?cellosaurus\.org/|web\.expasy\.org/cellosaurus/).+", re.IGNORECASE),
    "bitbucket": re.compile(r"https?://(?:www\.)?bitbucket\.org/.+", re.IGNORECASE),
    "xls": re.compile(r"https?://.+\.xls(?:\?.+)?", re.IGNORECASE),
    "ppt": re.compile(r"https?://.+\.ppt(?:\?.+)?", re.IGNORECASE),
    "jpg": re.compile(r"https?://.+\.jpg(?:\?.+)?", re.IGNORECASE),
    "png": re.compile(r"https?://.+\.png(?:\?.+)?", re.IGNORECASE),
}

DUD_PATTERNS = ["issues", "releases", "pull", "linkedin", "scopus", "adsabs", "faq", "enquiries-about-studies-not-listed-on-the-vivli-platform", "ourmember"]

def is_dud(link: str) -> bool:
    return any(dud in link.lower() for dud in DUD_PATTERNS)

# Helper function to remove anything after link regex endings below to remove the potential expiry codes
def strip_query_params(link: str) -> str:
    match = re.search(r'(?i)(\.pdf|\.xlsx|\.csv|\.rds|\.docx|\.zip)', link)
    if match:
        ext = match.group(1)
        return link[:link.find(ext) + len(ext)]
    return link

#Verify a link doesn't contain https:// more than once, if so, use the last occurence
def verify_single_https(link: str) -> str:
    matches = re.findall(r'https://[^\s,\'"]+', link)
    if matches:
        return matches[-1]
    return link

# Helper function to clean and categorize a link 
def classify_link(link: str):
    cleaned_link = strip_query_params(link)
    for subcat, pattern in SUPPLEMENTARY_PATTERNS.items():
        if pattern.search(cleaned_link):
            for group, subcats in SUPPLEMENTARY.items():
                if subcat in subcats:
                    return group, subcat
    return None, None

# Create supplementary object (resources object) for the publication going into the database
def classify_all(links: set[str]):
    result = {group: {subcat: [] for subcat in SUPPLEMENTARY[group]} for group in SUPPLEMENTARY}
    
    for link in links:
        if is_dud(link):
            continue
        group, subcat = classify_link(link)
        if group and subcat:
            cleaned = strip_query_params(link)
            if cleaned not in result[group][subcat]:
                result[group][subcat].append(cleaned)

    return result

