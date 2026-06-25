import logging
import re
from typing import List, Dict, Any
from Bio import Entrez
from research_agent.config import ENTREZ_EMAIL, MAX_RESULTS

# Configure logger for tracking NCBI API transactions
logger = logging.getLogger(__name__)

# NCBI requires an email address to identify the tool and user making requests.
# If no email is provided, NCBI may block requests or return errors.
if ENTREZ_EMAIL:
    Entrez.email = ENTREZ_EMAIL
else:
    logger.warning("ENTREZ_EMAIL is not set. NCBI PubMed requests might fail or get throttled.")

def search_pubmed(question: str) -> List[Dict[str, Any]]:
    """
    Search PubMed database for medical articles matching the search term.
    
    Args:
        question (str): The search query or question.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing metadata of found papers.
        
    Raises:
        RuntimeError: If the PubMed API request fails or returns an invalid response.
    """
    if not Entrez.email:
        logger.warning("Attempting to search PubMed without ENTREZ_EMAIL set.")

    logger.info(f"Initiating PubMed search for query: '{question}' (Max results: {MAX_RESULTS})")

    # Step 1: Query NCBI esearch to get matching PubMed IDs (PMIDs)
    try:
        handle = Entrez.esearch(db="pubmed", term=question, retmax=MAX_RESULTS)
        record = Entrez.read(handle)
        handle.close()
    except Exception as e:
        logger.error(f"NCBI esearch failed for query '{question}': {e}", exc_info=True)
        raise RuntimeError("Failed to query PubMed search engine.") from e

    ids = record.get("IdList", [])
    if not ids:
        logger.info(f"No papers matching the query '{question}' were found.")
        return []

    logger.info(f"Found {len(ids)} matching PubMed ID(s). Fetching metadata...")

    # Step 2: Fetch full XML records for the retrieved PMIDs
    try:
        handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
    except Exception as e:
        logger.error(f"NCBI efetch failed for IDs {ids}: {e}", exc_info=True)
        raise RuntimeError("Failed to fetch paper metadata from PubMed.") from e

    papers = []
    
    # Step 3: Parse details of each article from the XML response
    for article in records.get("PubmedArticle", []):
        try:
            med = article["MedlineCitation"]
            art = med["Article"]

            # Extract Title
            title = str(art.get("ArticleTitle", "")).strip()

            # Extract Abstract: Handles structured abstracts (which are returned as lists in XML)
            abstract_text = art.get("Abstract", {}).get("AbstractText", [])
            if isinstance(abstract_text, list):
                abstract = " ".join([str(section) for section in abstract_text if section]).strip()
            else:
                abstract = str(abstract_text).strip() if abstract_text else ""

            # Extract PMID
            pmid = str(med["PMID"])

            # Extract Publication Year (handles missing 'Year' by parsing 'MedlineDate')
            pub_date = art["Journal"]["JournalIssue"]["PubDate"]
            year = pub_date.get("Year", "")
            if not year and "MedlineDate" in pub_date:
                # Look for any 4 digit year in MedlineDate field (e.g. "2020 Dec-2021 Jan")
                match = re.search(r"\b(19|20)\d{2}\b", str(pub_date["MedlineDate"]))
                year = match.group(0) if match else str(pub_date["MedlineDate"])
            
            year = str(year).strip()

            # Extract Authors List
            authors = []
            for author in art.get("AuthorList", []):
                last_name = author.get("LastName", "")
                fore_name = author.get("ForeName", "")
                if last_name or fore_name:
                    authors.append(f"{last_name} {fore_name}".strip())

            papers.append({
                "title": title,
                "pmid": pmid,
                "abstract": abstract,
                "authors": authors,
                "year": year,
            })
        except KeyError as ke:
            # Log parsing errors for specific articles but continue processing others
            logger.warning(f"Missing expected XML field during parsing paper metadata: {ke}")
            continue
        except Exception as ex:
            logger.warning(f"Unexpected error parsing a PubMed article metadata record: {ex}")
            continue

    logger.info(f"Successfully parsed {len(papers)} papers from PubMed response.")
    return papers