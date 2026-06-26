from pydantic import BaseModel, Field
from typing import List, Optional

class QuestionInput(BaseModel):
    """
    Schema representing the incoming user request payload for research querying.
    """
    question: str = Field(
        ...,
        description="The medical research query or question to be searched on PubMed and ranked by BM25.",
        json_schema_extra={"placeholder": "E.g., What is the efficacy of immunotherapy in stage IV lung cancer?"}
    )

class Paper(BaseModel):
    """
    Schema representing a single medical article's metadata along with its BM25 relevance score.
    """
    title: str = Field(
        ..., 
        description="The title of the PubMed publication."
    )
    pmid: str = Field(
        ..., 
        description="PubMed Unique Identifier (PMID)."
    )
    abstract: str = Field(
        ..., 
        description="Concatenated text of the article's abstract."
    )
    authors: List[str] = Field(
        default_factory=list, 
        description="List of authors, formatted as 'LastName ForeName'."
    )
    year: Optional[str] = Field(
        None, 
        description="Publication year, fallback to MedlineDate string if specific year is not available."
    )
    score: float = Field(
        ..., 
        description="The calculated hybrid (BM25 + Semantic) relevance score relative to the question."
    )
    bm25_score: Optional[float] = Field(
        None,
        description="The individual BM25 relevance score before normalization."
    )
    semantic_score: Optional[float] = Field(
        None,
        description="The individual semantic relevance score before normalization."
    )
    is_cached: Optional[bool] = Field(
        False,
        description="Whether the paper was retrieved from local FAISS cache."
    )

class ResearchResponse(BaseModel):
    """
    Schema representing the unified research response returned by the agent.
    """
    question: str = Field(
        ..., 
        description="The original search query."
    )
    papers: List[Paper] = Field(
        ..., 
        description="The sorted list of top-ranked research papers relative to the query."
    )
    source: Optional[str] = Field(
        "pubmed",
        description="The source of the research results ('cached' or 'pubmed')."
    )