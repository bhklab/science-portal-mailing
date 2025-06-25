from pydantic import BaseModel
from typing import Optional, Union

class Publication(BaseModel):
    PMID: Optional[int] = -1
    doi: str
    date: str = None
    name: str = None
    journal: str = None
    type: str = None
    authors: str = None
    filteredAuthors: str = None
    affiliations: list[str] = None
    citations: int = 0
    dateAdded: str = None
    publisher: str = None
    status: Optional[str] = None
    image: Optional[str] = None
    scraped: Optional[bool] = None
    fanout: Optional[dict[str, Union[bool, None]]] = None
    supplementary: Optional[dict[str, dict[str, list[str]]]] = None
    otherLinks: Optional[list[dict]] = None
    submitter: str = 'routine'