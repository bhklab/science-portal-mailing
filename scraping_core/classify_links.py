import re
from urllib.parse import urlparse, parse_qs, urlunparse

SUPPLEMENTARY = {
    "code": ["github", "gitlab"],
    "data": [
        "geo", "dbgap", "kaggle", "dryad", "empiar", "gigadb", "zenodo", "ega", "xlsx", "csv",
        "proteinDataBank", "dataverse", "openScienceFramework", "finngenGitbook", "gtexPortal",
        "ebiAcUk", "mendeley", "R"
    ],
    "containers": ["codeocean", "colab"],
    "results": ["gsea", "figshare"],
    "trials": ["clinicalTrial", "euCTR", "vivli", "yoda"],
    "protocols": ["protocolsIO", "bioProtocol", "benchling", "labArchives"],
    "packages": ["bioconductor", "pypi", "CRAN"],
    "miscellaneous": ["IEEE", "pdf", "docx", "zip"]
}

SUPPLEMENTARY_PATTERNS = {
    "github": re.compile(r"^https?://(?:www\.)?github\.com/[\w\-]+/[\w\-]+(?:/[^/?#]+)?/?$", re.IGNORECASE),
    "gitlab": re.compile(r"https?://(?:www\.)?gitlab\.com/[\w\-]+/[\w\-]+(?:/.*)?", re.IGNORECASE),
    "geo": re.compile(r"https?://(?:www\.)?ncbi\.nlm\.nih\.gov/geo/query/acc\.cgi\?acc=GSE\d+|ftp://ftp\.ncbi\.nlm\.nih\.gov/geo/.+|https?://identifiers\.org/GEO:GSE\d+", re.IGNORECASE),
    "dbgap": re.compile(r"https?://(?:www\.)?ncbi\.nlm\.nih\.gov/projects/gap/cgi-bin/study\.cgi\?study_id=phs\d+", re.IGNORECASE),
	"kaggle": re.compile(r"https?://[^ ]*kaggle[^ ]*", re.IGNORECASE),
	"dryad": re.compile(r"https?://[^ ]*datadryad\.org/(?!($|stash/?$))[^ ]+|https?://[^ ]*doi\.org/10\.5061/dryad\.[^ ]+", re.IGNORECASE),
    "empiar": re.compile(r"https?://(?:www\.)?ebi\.ac\.uk/empiar/EMPIAR-\d+", re.IGNORECASE),
    "gigadb": re.compile(r"https?://(?:www\.)?gigadb\.org/dataset/\d+", re.IGNORECASE),
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
    "codeocean": re.compile(
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
    # "CRAN": re.compile(r"https?://(?:cran\.(r-project|rstudio)\.org|ggplot2\.tidyverse\.org)/web/packages/.+", re.IGNORECASE),
    # "IEEE": re.compile(r"https?://(?:www\.)?ieeexplore\.ieee\.org/document/\d+", re.IGNORECASE),
    "CRAN": re.compile(r"https?://[^ ]*cran[^ ]*", re.IGNORECASE),
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
    "labArchives": re.compile(r"https?://(?:www\.)?mynotebook\.labarchives\.com/.+", re.IGNORECASE)
}

SUPPLEMENTARY_LINK_PATTERN = re.compile(r"""
    https?://[^ \s<>"]+
""", re.IGNORECASE | re.VERBOSE)

DUD_PATTERNS = ["issues", "releases", "pull", "linkedin", "scopus", "adsabs", "faq", "enquiries-about-studies-not-listed-on-the-vivli-platform", "ourmember"]

def is_dud(link: str) -> bool:
    return any(dud in link.lower() for dud in DUD_PATTERNS)

def strip_query_params(link: str) -> str:
    match = re.search(r'(?i)(\.pdf|\.xlsx|\.csv|\.rds|\.docx|\.zip)', link)
    if match:
        ext = match.group(1)
        return link[:link.find(ext) + len(ext)]
    return link

def classify_link(link: str):
    cleaned_link = strip_query_params(link)
    for subcat, pattern in SUPPLEMENTARY_PATTERNS.items():
        if pattern.search(cleaned_link):
            for group, subcats in SUPPLEMENTARY.items():
                if subcat in subcats:
                    return group, subcat
    return None, None

def classify_all(links: set[str]):
    result = {group: {subcat: [] for subcat in SUPPLEMENTARY[group]} for group in SUPPLEMENTARY}

    for link in links:
        if is_dud(link):
            continue
        group, subcat = classify_link(link)
        if group and subcat:
            cleaned = strip_query_params(link)
            result[group][subcat].append(cleaned)

    return result

