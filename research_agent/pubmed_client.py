import logging
import re
from typing import List, Dict, Any
from Bio import Entrez
from research_agent.config import ENTREZ_EMAIL, MAX_RESULTS, NCBI_API_KEY

# Configure logger for tracking NCBI API transactions
logger = logging.getLogger(__name__)

# NCBI requires an email address to identify the tool and user making requests.
if ENTREZ_EMAIL:
    Entrez.email = ENTREZ_EMAIL
else:
    logger.warning("ENTREZ_EMAIL is not set. NCBI PubMed requests might fail or get throttled.")

if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY
    logger.info("NCBI_API_KEY is configured and set in Biopython Entrez.")

def parse_single_article(article: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse a single PubmedArticle XML record into structured metadata."""
    try:
        med = article.get("MedlineCitation")
        if not med:
            logger.warning("Skipping PubMed article due to missing MedlineCitation element.")
            return None
            
        art = med.get("Article")
        if not art:
            logger.warning("Skipping PubMed article due to missing Article element inside MedlineCitation.")
            return None

        # Extract Title safely
        title = str(art.get("ArticleTitle", "")).strip()

        # Extract Abstract safely: Handles structured abstracts
        abstract = ""
        abstract_dict = art.get("Abstract")
        if isinstance(abstract_dict, dict):
            abstract_text = abstract_dict.get("AbstractText", [])
            if isinstance(abstract_text, list):
                abstract = " ".join([str(section) for section in abstract_text if section]).strip()
            elif abstract_text:
                abstract = str(abstract_text).strip()

        # Extract PMID safely
        pmid = str(med.get("PMID", "")).strip()
        if not pmid:
            logger.warning("Skipping PubMed article due to missing PMID.")
            return None

        # Extract Publication Year (handles missing 'Year' by parsing 'MedlineDate') safely
        year = ""
        journal = art.get("Journal")
        if isinstance(journal, dict):
            journal_issue = journal.get("JournalIssue")
            if isinstance(journal_issue, dict):
                pub_date = journal_issue.get("PubDate")
                if isinstance(pub_date, dict):
                    year = pub_date.get("Year", "")
                    if not year and "MedlineDate" in pub_date:
                        match = re.search(r"\b(19|20)\d{2}\b", str(pub_date["MedlineDate"]))
                        year = match.group(0) if match else str(pub_date["MedlineDate"])
        
        year = str(year).strip() if year else None

        # Extract Authors List safely (supporting standard names and collective names)
        authors = []
        author_list = art.get("AuthorList", [])
        if isinstance(author_list, list):
            for author in author_list:
                if not isinstance(author, dict):
                    continue
                last_name = author.get("LastName", "")
                fore_name = author.get("ForeName", "")
                collective_name = author.get("CollectiveName", "")
                if last_name or fore_name:
                    authors.append(f"{last_name} {fore_name}".strip())
                elif collective_name:
                    authors.append(str(collective_name).strip())

        return {
            "title": title,
            "pmid": pmid,
            "abstract": abstract,
            "authors": authors,
            "year": year,
        }
    except Exception as ex:
        logger.warning(f"Unexpected error parsing a PubMed article metadata record: {ex}", exc_info=True)
        return None

def parse_pubmed_records(records: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse a dictionary of PubMed records into structured paper metadata."""
    papers = []
    for article in records.get("PubmedArticle", []):
        parsed = parse_single_article(article)
        if parsed:
            papers.append(parsed)
    return papers

def clean_query(question: str) -> str:
    """Strip conversational words, keep medical terms."""
    stopwords = {
        "what", "are", "the", "is", "does", "do", "can", "how", "why",
        "when", "which", "a", "an", "of", "in", "on", "for", "to",
        "long", "term", "effects", "relationship", "between", "reduce",
        "risk", "cause", "effective"
    }
    tokens = re.findall(r'\b[a-zA-Z0-9\-]+\b', question.lower())
    filtered = [t for t in tokens if t not in stopwords]
    return " ".join(filtered)

def search_pubmed(question: str) -> List[Dict[str, Any]]:
    """Search PubMed database for medical articles matching the search term."""
    if not Entrez.email:
        logger.warning("Attempting to search PubMed without ENTREZ_EMAIL set.")

    query = clean_query(question)
    logger.info(f"Initiating PubMed search for query: '{question}' (Cleaned: '{query}') (Max results: {MAX_RESULTS})")

    # Step 1: Query NCBI esearch to get matching PubMed IDs (PMIDs)
    try:
        with Entrez.esearch(db="pubmed", term=query, retmax=MAX_RESULTS) as handle:
            record = Entrez.read(handle)
    except Exception as e:
        logger.error(f"NCBI esearch failed for query '{query}': {e}", exc_info=True)
        raise RuntimeError("Failed to query PubMed search engine.") from e

    ids = record.get("IdList", [])
    if not ids:
        logger.info(f"No papers matching the query '{query}' were found.")
        return []

    logger.info(f"Found {len(ids)} IDs. Fetching in single batch...")

    # Step 2: Fetch full XML records in a single call (fastest and safe from rate-limiting)
    try:
        with Entrez.efetch(db="pubmed", id=",".join(ids), rettype="xml", retmode="xml") as handle:
            records = Entrez.read(handle)
    except Exception as e:
        logger.error(f"NCBI efetch failed for IDs {ids}: {e}", exc_info=True)
        raise RuntimeError("Failed to fetch paper metadata from PubMed.") from e

    return parse_pubmed_records(records)