from pydantic import BaseModel
from typing import Optional, Union

class Publication(BaseModel):
    PMID: Optional[int] = -1
    doi: str
    date: Optional[str] = None
    name: Optional[str] = None
    journal: Optional[str] = None
    type: Optional[str] = None
    authors: Optional[str] = None
    filteredAuthors: Optional[str] = None
    affiliations: Optional[list[str]] = []
    citations: Optional[int] = 0
    dateAdded: Optional[str] = None
    publisher: Optional[str] = None
    status: Optional[str] = None
    image: Optional[str] = None
    scraped: Optional[bool] = None
    fanout: Optional[dict[str, Union[bool, None]]] = None
    supplementary: Optional[dict[str, dict[str, list[str]]]] = None
    otherLinks: Optional[list[dict]] = None
    submitter: str = 'routine'