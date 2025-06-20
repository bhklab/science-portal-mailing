from pydantic import BaseModel
from typing import Optional

class Publication(BaseModel):
    PMID: Optional[int] = -1
    doi: str
    date: str
    name: str
    journal: str
    type: str
    authors: str
    filteredAuthors: str
    affiliations: list[str]
    citations: int
    dateAdded: str
    publisher: str
    status: str
    image: Optional[str] = None
    scraped: bool
    fanout: Optional[dict[str, bool]] = None
    supplementary: Optional[dict[str, dict[str, list[str]]]] = None
    otherLinks: Optional[list[dict]] = None
    submitter: str   