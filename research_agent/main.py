import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from research_agent.models import QuestionInput, ResearchResponse, Paper
from research_agent.pubmed_client import search_pubmed
from research_agent.bm25_ranker import rank_papers
from research_agent.config import TOP_K
from research_agent.faiss_store import save_to_store, search_store
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
    Search local FAISS database first for semantic matches, falling back to NCBI PubMed
    if not cached. Newly fetched papers are embedded and cached to FAISS, and ranked.
    """
    if not input.question.strip():
        raise HTTPException(
            status_code=400, 
            detail="Question cannot be empty or contain only whitespace"
        )

    start = time.time()
    logger.info(f"Received research request for query: '{input.question}'")

    # 1. Try FAISS first
    try:
        query_vec = embed_single(input.question)
        cached = search_store(query_vec, top_k=TOP_K)
    except Exception as e:
        logger.warning(f"FAISS search failed, falling back to PubMed: {e}", exc_info=True)
        cached = None

    if cached:
        logger.info("Serving results from FAISS cache.")
        return ResearchResponse(
            question=input.question,
            papers=[Paper(**p) for p in cached]
        )

    # 2. Fallback to PubMed
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

    # 3. Embed and save to FAISS
    try:
        texts = [p["title"] + " " + p["abstract"] for p in papers]
        embeddings = embed_texts(texts)
        save_to_store(embeddings, papers)
    except Exception as e:
        logger.error(f"Failed to embed/save publications to FAISS cache: {e}", exc_info=True)
        # We continue to rank and return results even if caching fails

    # 4. Rank and return
    try:
        ranked = rank_papers(input.question, papers)
    except Exception as e:
        logger.error(f"Ranking algorithm failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to rank the retrieved research papers."
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