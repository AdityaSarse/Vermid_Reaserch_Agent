import os
import json
import logging
import numpy as np
import faiss

logger = logging.getLogger(__name__)

INDEX_PATH = "faiss_store/index.faiss"
METADATA_PATH = "faiss_store/metadata.json"
DIMENSION = 768  # PubMed-BERT embedding size

def _ensure_dir():
    os.makedirs("faiss_store", exist_ok=True)

def save_to_store(embeddings: np.ndarray, papers: list):
    _ensure_dir()

    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH) as f:
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
    faiss.normalize_L2(vecs)
    index.add(vecs)
    metadata.extend(new_papers)

    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f)

    logger.info(f"Added {len(new_papers)} new papers to FAISS store. Total: {len(metadata)}")

def search_store(query_embedding: np.ndarray, top_k: int = 5):
    if not os.path.exists(INDEX_PATH):
        logger.info("FAISS store not found. Falling back to PubMed.")
        return None

    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    vec = np.array([query_embedding]).astype("float32")
    faiss.normalize_L2(vec)

    scores, indices = index.search(vec, top_k)

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

def search_store_full(query_embedding: np.ndarray, top_k: int = 20):
    """Return more candidates from FAISS for hybrid reranking."""
    if not os.path.exists(INDEX_PATH):
        return None, None

    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    vec = np.array([query_embedding]).astype("float32")
    faiss.normalize_L2(vec)

    k = min(top_k, index.ntotal)
    scores, indices = index.search(vec, k)

    results = []
    semantic_scores = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append(metadata[idx].copy())
        semantic_scores.append(float(score))

    logger.info(f"FAISS returned {len(results)} candidates for hybrid reranking.")
    return results, semantic_scores
