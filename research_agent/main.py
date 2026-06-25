import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from research_agent.models import QuestionInput, ResearchResponse, Paper
from research_agent.pubmed_client import search_pubmed
from research_agent.bm25_ranker import rank_papers

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

@app.post(
    "/research",
    response_model=ResearchResponse,
    summary="Search PubMed and Rank by Relevance",
    response_description="The matched papers sorted by relevance score."
)
def research(input: QuestionInput):
    """
    Search NCBI PubMed for papers matching the user's question,
    calculate BM25 relevance scores across abstracts, and return
    the ranked results.
    """
    # Clean input question
    query_text = input.question.strip()
    if not query_text:
        raise HTTPException(
            status_code=400, 
            detail="Question cannot be empty or contain only whitespace"
        )

    start_time = time.time()
    logger.info(f"Received research request for query: '{query_text}'")

    # Fetch papers from NCBI PubMed
    try:
        papers = search_pubmed(query_text)
    except RuntimeError as re:
        # Gracefully handle known integration/network failures
        logger.error(f"NCBI PubMed API error during query: {re}")
        raise HTTPException(
            status_code=503,
            detail="PubMed service is temporarily unavailable. Please try again later."
        )
    except Exception as e:
        # Handle other unexpected runtime exceptions to prevent full server crashes
        logger.error(f"Unexpected error retrieving publications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing research results."
        )

    # If no results are returned, inform the client with a 404 Status
    if not papers:
        raise HTTPException(
            status_code=404, 
            detail=f"No PubMed articles found matching the term: '{query_text}'"
        )

    # Rank the papers using BM25
    try:
        ranked_papers = rank_papers(query_text, papers)
    except Exception as e:
        logger.error(f"Ranking algorithm failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to rank the retrieved research papers."
        )

    elapsed_time = round(time.time() - start_time, 2)
    logger.info(f"Request resolved in {elapsed_time}s. Returning top {len(ranked_papers)} papers.")

    # Return structured response
    return ResearchResponse(
        question=query_text,
        papers=[Paper(**p) for p in ranked_papers]
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