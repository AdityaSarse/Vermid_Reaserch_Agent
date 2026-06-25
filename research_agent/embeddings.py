import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

MODEL_NAME = "pritamdeka/S-PubMedBert-MS-MARCO"

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded.")
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, show_progress_bar=False)

def score_papers_semantic(question: str, papers: list) -> list:
    texts = [p["title"] + " " + p["abstract"] for p in papers]
    
    question_vec = embed_texts([question])
    paper_vecs = embed_texts(texts)
    
    scores = cosine_similarity(question_vec, paper_vecs)[0]
    
    for i, paper in enumerate(papers):
        paper["semantic_score"] = round(float(scores[i]), 4)
    
    return papers

def embed_single(text: str) -> np.ndarray:
    model = get_model()
    return model.encode([text])[0]
