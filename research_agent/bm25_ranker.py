import re
import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from research_agent.config import TOP_K
from research_agent.embeddings import score_papers_semantic

logger = logging.getLogger(__name__)

BM25_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6

def tokenize(text: str) -> List[str]:
    """
    Clean and tokenize text by converting to lowercase, stripping HTML/XML tags,
    and stripping punctuation.
    This guarantees that terms with trailing punctuation match query terms correctly.
    
    Args:
        text (str): The text to tokenize.
        
    Returns:
        List[str]: A list of clean, lowercase tokens.
    """
    if not text:
        return []
    # Strip HTML/XML tags if present
    cleaned_text = re.sub(r"<[^>]+>", "", text)
    # Using regex to extract words (alphanumeric sequences), discarding punctuation
    return re.findall(r"\b\w+\b", cleaned_text.lower())

def rank_papers(question: str, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank PubMed papers against a query question using a hybrid scoring algorithm:
    Combines normalized BM25 Okapi scores (40%) and normalized semantic embedding scores (60%).
    
    Args:
        question (str): The query question.
        papers (List[Dict[str, Any]]): The list of paper metadata dictionaries to rank.
        
    Returns:
        List[Dict[str, Any]]: The top K ranked papers sorted by their hybrid relevance score in descending order.
    """
    # Guard against empty paper list inputs to avoid BM25 library computation errors
    if not papers:
        logger.info("Empty papers list provided to BM25 ranker. Returning empty results.")
        return []

    logger.info(f"Ranking {len(papers)} papers using Hybrid BM25 + Semantic for question: '{question}'")

    # Step 1: BM25 Scoring
    corpus = []
    for p in papers:
        # Gracefully handle missing title/abstract keys
        title = p.get("title", "") or ""
        abstract = p.get("abstract", "") or ""
        full_text = f"{title} {abstract}"
        corpus.append(tokenize(full_text))

    bm25 = BM25Okapi(corpus)
    query_tokens = tokenize(question)
    
    # Guard against empty query tokens (e.g. only punctuation like "???")
    if not query_tokens:
        logger.warning(f"No valid tokens found in question: '{question}'. Setting BM25 scores to 0.0.")
        bm25_scores = [0.0] * len(papers)
    else:
        bm25_scores = bm25.get_scores(query_tokens)

    for i, paper in enumerate(papers):
        paper["bm25_score"] = round(float(bm25_scores[i]), 4)

    # Step 2: Semantic Scoring (using sentence transformers)
    papers = score_papers_semantic(question, papers)

    # Step 3: Normalization and Hybrid scoring (Normalize both scores to [0, 1])
    bm25_vals = [p["bm25_score"] for p in papers]
    sem_vals = [p["semantic_score"] for p in papers]

    bm25_max = max(bm25_vals) or 1.0
    sem_max = max(sem_vals) or 1.0

    # Ensure max values are positive for safe division
    if bm25_max <= 0:
        bm25_max = 1.0
    if sem_max <= 0:
        sem_max = 1.0

    for paper in papers:
        norm_bm25 = max(0.0, paper["bm25_score"]) / bm25_max
        norm_sem = max(0.0, paper["semantic_score"]) / sem_max
        paper["score"] = round(
            BM25_WEIGHT * norm_bm25 + SEMANTIC_WEIGHT * norm_sem, 4
        )

    # Step 4: Sort papers in descending order of Hybrid score
    ranked = sorted(papers, key=lambda x: x.get("score", 0.0), reverse=True)
    
    logger.info(f"Hybrid ranking complete. Returning top {min(len(ranked), TOP_K)} papers.")
    return ranked[:TOP_K]

def hybrid_rerank(question: str, papers: List[Dict[str, Any]], semantic_scores: List[float], top_k: int = None) -> List[Dict[str, Any]]:
    """
    Rerank a list of papers using a hybrid scoring algorithm with pre-computed semantic scores:
    Combines normalized BM25 scores (40% weight) and pre-computed normalized semantic scores (60% weight).
    """
    from research_agent.config import TOP_K
    top_k = top_k or TOP_K

    if not papers:
        return []

    # Step 1: BM25 Scoring
    corpus = []
    for p in papers:
        # Gracefully handle missing title/abstract keys
        title = p.get("title", "") or ""
        abstract = p.get("abstract", "") or ""
        full_text = f"{title} {abstract}"
        corpus.append(tokenize(full_text))

    bm25 = BM25Okapi(corpus)
    query_tokens = tokenize(question)
    
    # Guard against empty query tokens
    if not query_tokens:
        logger.warning(f"No valid tokens found in question: '{question}' during reranking. Setting BM25 scores to 0.0.")
        bm25_scores = [0.0] * len(papers)
    else:
        bm25_scores = bm25.get_scores(query_tokens)

    # Step 2: Normalization and Hybrid scoring (Normalize both scores to [0, 1])
    bm25_max = max(bm25_scores) or 1.0
    sem_max = max(semantic_scores) or 1.0

    # Ensure max values are positive for safe division
    if bm25_max <= 0:
        bm25_max = 1.0
    if sem_max <= 0:
        sem_max = 1.0

    for i, paper in enumerate(papers):
        raw_bm25 = float(bm25_scores[i])
        raw_sem = float(semantic_scores[i])

        norm_bm25 = max(0.0, raw_bm25) / bm25_max
        norm_sem = max(0.0, raw_sem) / sem_max

        paper["bm25_score"] = round(raw_bm25, 4)
        paper["semantic_score"] = round(raw_sem, 4)
        paper["score"] = round(BM25_WEIGHT * norm_bm25 + SEMANTIC_WEIGHT * norm_sem, 4)

    # Step 3: Sort papers in descending order of Hybrid score
    ranked = sorted(papers, key=lambda x: x.get("score", 0.0), reverse=True)
    logger.info(f"V4 Hybrid reranking complete. Returning top {min(len(ranked), top_k)} papers.")
    return ranked[:top_k]