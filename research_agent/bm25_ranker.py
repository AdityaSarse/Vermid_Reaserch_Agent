import re
import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from research_agent.config import TOP_K

logger = logging.getLogger(__name__)

def tokenize(text: str) -> List[str]:
    """
    Clean and tokenize text by converting to lowercase and stripping punctuation.
    This guarantees that terms with trailing punctuation match query terms correctly.
    
    Args:
        text (str): The text to tokenize.
        
    Returns:
        List[str]: A list of clean, lowercase tokens.
    """
    if not text:
        return []
    # Using regex to extract words (alphanumeric sequences), discarding punctuation
    return re.findall(r"\b\w+\b", text.lower())

def rank_papers(question: str, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank PubMed papers against a query question using the BM25Okapi ranking algorithm.
    
    Args:
        question (str): The query question.
        papers (List[Dict[str, Any]]): The list of paper metadata dictionaries to rank.
        
    Returns:
        List[Dict[str, Any]]: The top K ranked papers sorted by their BM25 score in descending order.
    """
    # Guard against empty paper list inputs to avoid BM25 library computation errors
    if not papers:
        logger.info("Empty papers list provided to BM25 ranker. Returning empty results.")
        return []

    logger.info(f"Ranking {len(papers)} papers using BM25 for question: '{question}'")

    # Step 1: Build the corpus by tokenizing title + abstract of each paper
    corpus = []
    for p in papers:
        # Gracefully handle missing title/abstract keys
        title = p.get("title", "") or ""
        abstract = p.get("abstract", "") or ""
        full_text = f"{title} {abstract}"
        corpus.append(tokenize(full_text))

    # Step 2: Initialize BM25Okapi ranker and calculate relevance scores
    bm25 = BM25Okapi(corpus)
    query_tokens = tokenize(question)
    scores = bm25.get_scores(query_tokens)

    # Step 3: Map calculated scores back to each paper object
    for i, paper in enumerate(papers):
        # Round the BM25 score to 4 decimal places for presentation
        paper["score"] = round(float(scores[i]), 4)

    # Step 4: Sort papers in descending order of BM25 score
    ranked = sorted(papers, key=lambda x: x.get("score", 0.0), reverse=True)
    
    logger.info(f"Ranking complete. Returning top {min(len(ranked), TOP_K)} papers.")
    return ranked[:TOP_K]