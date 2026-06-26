import os
import json
import hashlib
import logging
import numpy as np
import faiss

logger = logging.getLogger(__name__)

DIMENSION = 768  # PubMed-BERT embedding size
SIMILARITY_THRESHOLD = 0.75
BASE_DIR = "faiss_store"

def _get_store_path(question: str):
    """Each question gets its own store based on a hash of the question."""
    key = hashlib.md5(question.lower().strip().encode()).hexdigest()[:10]
    folder = os.path.join(BASE_DIR, key)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "index.faiss"), os.path.join(folder, "metadata.json")

def save_to_store(embeddings: np.ndarray, papers: list, question: str):
    index_path, metadata_path = _get_store_path(question)

    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        with open(metadata_path) as f:
            metadata = json.load(f)
    else:
        index = faiss.IndexFlatIP(DIMENSION)  # Inner product = cosine on normalized vecs
        metadata = []

    # Avoid duplicates by PMID
    existing_pmids = {p["pmid"] for p in metadata}
    new_papers = []
    new_embeddings = []

    for i, paper in enumerate(papers):
        if paper["pmid"] not in existing_pmids:
            new_papers.append(paper)
            new_embeddings.append(embeddings[i])

    if not new_papers:
        logger.info("No new papers to add to FAISS store.")
        return

    vecs = np.array(new_embeddings).astype("float32")
    index.add(vecs)
    metadata.extend(new_papers)

    faiss.write_index(index, index_path)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    logger.info(f"Saved {len(new_papers)} papers for this query. Total: {len(metadata)}")

def search_store(query_embedding: np.ndarray, question: str, top_k: int = 5):
    index_path, metadata_path = _get_store_path(question)

    if not os.path.exists(index_path):
        logger.info("FAISS store not found for this query.")
        return None

    index = faiss.read_index(index_path)
    with open(metadata_path) as f:
        metadata = json.load(f)

    vec = np.array([query_embedding]).astype("float32")

    k = min(top_k, index.ntotal)
    scores, indices = index.search(vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        paper = metadata[idx].copy()
        paper["semantic_score"] = round(float(score), 4)
        paper["score"] = round(float(score), 4)
        results.append(paper)

    logger.info(f"FAISS returned {len(results)} results from local store.")
    return results

def search_store_full(query_embedding: np.ndarray, question: str, top_k: int = 20):
    """Return more candidates from FAISS for hybrid reranking."""
    index_path, metadata_path = _get_store_path(question)

    if not os.path.exists(index_path):
        logger.info("No FAISS store for this query. Falling back to PubMed.")
        return None, None

    index = faiss.read_index(index_path)
    with open(metadata_path) as f:
        metadata = json.load(f)

    vec = np.array([query_embedding]).astype("float32")

    k = min(top_k, index.ntotal)
    scores, indices = index.search(vec, k)

    results = []
    semantic_scores = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or score < SIMILARITY_THRESHOLD:
            continue
        results.append(metadata[idx].copy())
        semantic_scores.append(float(score))

    if not results:
        logger.info("FAISS results below threshold. Treating as cache miss.")
        return None, None

    logger.info(f"FAISS returned {len(results)} results above threshold {SIMILARITY_THRESHOLD} for this query.")
    return results, semantic_scores
