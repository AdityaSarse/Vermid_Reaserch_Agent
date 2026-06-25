import time
import logging
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from research_agent.models import QuestionInput, ResearchResponse, Paper
from research_agent.pubmed_client import search_pubmed
from research_agent.bm25_ranker import rank_papers, hybrid_rerank
from research_agent.config import TOP_K
from research_agent.faiss_store import save_to_store, search_store_full
from research_agent.embeddings import embed_texts, embed_single

# Configure logging format and levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with basic metadata
app = FastAPI(
    title="VeriMed-X Research Agent",
    description=(
        "An intelligent medical search and ranking agent. It queries NCBI PubMed, "
        "concatenates abstracts, and ranks them by semantic relevance using BM25."
    ),
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing) middleware to allow browser-based
# frontends (e.g. React, Vue, Next.js, or static dashboards) to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific domains in a production environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from research_agent.embeddings import get_model

@app.on_event("startup")
async def startup_event():
    logger.info("Pre-loading embedding model...")
    get_model()
    logger.info("Model ready.")

@app.post(
    "/research",
    response_model=ResearchResponse,
    summary="Search PubMed and Rank by Relevance",
    response_description="The matched papers sorted by relevance score."
)
def research(input: QuestionInput):
    """
    Search local FAISS database first using query embeddings. If cached candidates are found,
    re-rank them via hybrid ranking. Otherwise, fallback to NCBI PubMed, fetch, embed,
    cache to FAISS, and then compute cosine similarity and re-rank.
    """
    if not input.question.strip():
        raise HTTPException(
            status_code=400, 
            detail="Question cannot be empty or contain only whitespace"
        )

    start = time.time()
    logger.info(f"Received research request for query: '{input.question}'")

    # 1. Embed query
    try:
        query_vec = embed_single(input.question)
    except Exception as e:
        logger.error(f"Embedding query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embedding for the query."
        )

    # 2. FAISS search — get candidates + semantic scores
    try:
        papers, semantic_scores = search_store_full(query_vec, top_k=20)
    except Exception as e:
        logger.warning(f"FAISS search failed, falling back to PubMed: {e}", exc_info=True)
        papers, semantic_scores = None, None

    if papers:
        # 3a. Hybrid rerank from FAISS candidates
        try:
            ranked = hybrid_rerank(input.question, papers, semantic_scores)
            logger.info("V4 Hybrid rerank from FAISS cache.")
        except Exception as e:
            logger.error(f"Reranking FAISS candidates failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to rank cached publications."
            )
    else:
        # 3b. Fallback — fetch from PubMed
        try:
            papers = search_pubmed(input.question)
        except RuntimeError as re:
            logger.error(f"NCBI PubMed API error during query: {re}")
            raise HTTPException(
                status_code=503,
                detail="PubMed service is temporarily unavailable. Please try again later."
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving publications: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An internal server error occurred while processing research results."
            )

        if not papers:
            raise HTTPException(
                status_code=404, 
                detail=f"No PubMed articles found matching the term: '{input.question}'"
            )

        # Embed, save, and compute cosine similarity scores for hybrid reranking
        try:
            texts = [p["title"] + " " + p["abstract"] for p in papers]
            embeddings = embed_texts(texts)
            save_to_store(embeddings, papers)
            
            # Compute cosine similarity: dot product of normalized vectors
            # embed_single returns 1D array, normalize it
            q_norm = np.linalg.norm(query_vec)
            q_norm_val = q_norm if q_norm > 0 else 1.0
            
            semantic_scores = []
            for e in embeddings:
                e_norm = np.linalg.norm(e)
                e_norm_val = e_norm if e_norm > 0 else 1.0
                score = float(np.dot(query_vec, e) / (q_norm_val * e_norm_val))
                semantic_scores.append(score)
        except Exception as e:
            logger.error(f"Failed to embed or save publications to FAISS cache: {e}", exc_info=True)
            # Fallback to standard ranking if embedding/caching fails entirely
            try:
                ranked = rank_papers(input.question, papers)
                elapsed = round(time.time() - start, 2)
                logger.info(f"Request resolved in {elapsed}s using basic ranker. Returning top {len(ranked)} papers.")
                return ResearchResponse(
                    question=input.question,
                    papers=[Paper(**p) for p in ranked]
                )
            except Exception as ex:
                logger.error(f"Fallback ranking failed: {ex}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to rank retrieved publications."
                )

        try:
            ranked = hybrid_rerank(input.question, papers, semantic_scores)
            logger.info("V4 Hybrid rerank from fresh PubMed fetch.")
        except Exception as e:
            logger.error(f"Hybrid reranking after PubMed fetch failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to rank retrieved publications."
            )

    elapsed = round(time.time() - start, 2)
    logger.info(f"Request resolved in {elapsed}s. Returning top {len(ranked)} papers.")

    return ResearchResponse(
        question=input.question,
        papers=[Paper(**p) for p in ranked]
    )

@app.get(
    "/health",
    summary="Check API Health Status",
    response_description="A status dictionary confirming the service is online and how it is configured."
)
def health():
    """
    Check the health of the service and verify if critical environment variables are set up.
    """
    from research_agent.config import ENTREZ_EMAIL
    email_configured = bool(ENTREZ_EMAIL and ENTREZ_EMAIL.strip())
    
    return {
        "status": "healthy",
        "ncbi_email_configured": email_configured
    }