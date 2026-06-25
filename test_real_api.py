import logging
import sys
from research_agent.pubmed_client import search_pubmed
from research_agent.bm25_ranker import rank_papers

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)

try:
    print("--- Starting Live PubMed API Integration Test ---")
    query = "lung cancer immunotherapy"
    print(f"Searching PubMed for query: '{query}'...")
    papers = search_pubmed(query)
    print(f"Successfully retrieved {len(papers)} papers!")
    
    if not papers:
        print("Warning: No papers found. Check connection or query.")
    else:
        for i, p in enumerate(papers[:3]):
            print(f"Paper {i+1}:")
            print(f"  PMID:   {p.get('pmid')}")
            print(f"  Title:  {p.get('title')}")
            print(f"  Year:   {p.get('year')}")
            print(f"  Authors:{p.get('authors')}")
            print()
            
        print(f"Ranking papers for query: '{query}'...")
        ranked = rank_papers(query, papers)
        print("Top Ranked Results:")
        for i, p in enumerate(ranked[:3]):
            print(f"  {i+1}. Score: {p.get('score')} | PMID: {p.get('pmid')} | Title: {p.get('title')}")
            
    print("--- Live Test Finished Successfully ---")
except Exception as e:
    print("\n--- Error Occurred During Live Integration Test ---", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
sys.exit(0)
