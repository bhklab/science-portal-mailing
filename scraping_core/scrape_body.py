from dotenv import load_dotenv
import re

GSE_MENTION_PATTERN = re.compile(r"\bGSE\s?-?\s?(\d{4,6})\b", re.IGNORECASE)
NCT_MENTION_PATTERN = re.compile(r"\bNCT[\s-]?(\d{8})\b", re.IGNORECASE)

load_dotenv()

def scrape_body(body_text: str):

    links = set()

    matches = GSE_MENTION_PATTERN.findall(str(body_text))
    for gse_id in matches:
        gse_link = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE{gse_id}"
        links.add(gse_link)

    matches = NCT_MENTION_PATTERN.findall(body_text)
    for nct_id in matches:
        nct_link = f"https://clinicaltrials.gov/ct2/show/NCT{nct_id}"
        links.add(nct_link)

    print(f"Extracted {len(links)} GSE/NCT links")
    
    return links