from dotenv import load_dotenv
import os
import json
import pathlib
from typing import Optional, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


# Load environment variables
load_dotenv()
print("GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))
client = genai.Client()

# find the PDF file
pdf_path = pathlib.Path("/Users/Zeas/Desktop/uhn/science-portal-mailing/LLM_testing/data/#94.pdf")
output_file = "extracted_pub.json"


# Define the Pub schema for resources
class Supplementary(BaseModel):
    code: Optional[List[str]] = None
    data: Optional[List[str]] = None
    containers: Optional[List[str]] = None
    results: Optional[List[str]] = None
    trials: Optional[List[str]] = None
    protocols: Optional[List[str]] = None
    packages: Optional[List[str]] = None
    miscellaneous: Optional[List[str]] = None
    cellLines: Optional[List[str]] = None
    animalModels: Optional[List[str]] = None
    plasmids: Optional[List[str]] = None

# Define the OtherLink schema for new links
class OtherLink(BaseModel):
    name: str = ""
    recommendedCategory: str = ""
    description: str = ""
    link: str = ""

# Define the Pub schema for publication information
class Pub(BaseModel):
    PMID: int = -1
    doi: str = ""
    date: str = ""
    name: str = ""
    journal: str = ""
    type: str = ""
    authors: str = ""
    filteredAuthors: str = ""
    affiliations: List[str] = [""]
    citations: int = 0
    dateAdded: str = ""
    publisher: str = ""
    status: str = "Published"
    image: str = ""
    scraped: bool = False
    supplementary: Supplementary = Field(default_factory=Supplementary)
    otherLinks: List[OtherLink] = []
    submitter: str = ""

# Define the prompt for the Gemini model
prompt = """
You are an expert in extracting publication resources from scientific publications.
Your task: Fill the "supplementary" field of the provided Pub schema with the categorized resources found in the PDF text.
Rules:
-Bedfor scraping for resources fill out all the other information in the Pub schema.
- Use the Pub schema provided.
- Only include explicitly present resources (with working URLs or accession numbers).
- Use the correct category fields inside supplementary (code, data, trials, etc.).
- Do not include citations, or resources without URLs/accessions.
- Do not include urls or accesions obtained in references unless their url or accesion number is explicitly mentioned in the text do not generate a url for this it is better to just omit it.
- If a resource does not fit a predefined category, put it into otherLinks.
- If a link or accesion code has been sorted into one category, do not duplicate it in another.
GitHub goes into Code
GitLab goes into Code

GEO goes into Data
dbGaP goes into Data
Kaggle goes into Data
Dryad goes into Data
EMPIAR goes into Data
GigaDB goes into Data
Zenodo goes into Data
EGA goes into Data
XLSX goes into Data
CSV goes into Data
Protein Data Bank goes into Data
Dataverse goes into Data
Open Science Framework goes into Data
FinnGen Gitbook goes into Data
GTEx Portal goes into Data
EBI (ebi.ac.uk) goes into Data
Mendeley goes into Data
R goes into Data

CodeOcean goes into Containers
Google Colab goes into Containers

GSEA goes into Results
Figshare goes into Results

ClinicalTrials.gov goes into Trials
EU Clinical Trials Register (EUCTR) goes into Trials
Vivli goes into Trials
Yoda goes into Trials

Protocols.io goes into Protocols
BioProtocol goes into Protocols
Benchling goes into Protocols
LabArchives goes into Protocols

Bioconductor goes into Packages
PyPI goes into Packages
CRAN goes into Packages

IEEE goes into Miscellaneous
PDF goes into Miscellaneous
DOCX goes into Miscellaneous
ZIP goes into Miscellaneous

[] goes into CellLines
[] goes into AnimalModels
[] goes into Plasmids

- if a resource does fits into one of the above categories but was not named put it into the otherLinks field.
- if a link is not present remove that submission
- Respond with valid JSON strictly matching the Pub schema.
"""

# Generate content using the Gemini model
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=pdf_path.read_bytes(),
            mime_type="application/pdf",
        ),
        prompt
    ],
    config={
        "response_mime_type": "application/json",
        "response_schema": Pub,
    },
)

# Parse the response and save it to a JSON file
pub = response.parsed
with open(output_file, "w") as f:
    json.dump(pub.model_dump(by_alias=True), f, indent=2)

print(f"Publication JSON saved to {output_file}")
