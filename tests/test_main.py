import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from fastapi import HTTPException
from research_agent.models import QuestionInput

try:
    from fastapi.testclient import TestClient
    from research_agent.main import app
    client = TestClient(app)
    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False

class TestMain(unittest.TestCase):
    def test_health_endpoint(self):
        if HAS_TEST_CLIENT:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "healthy")
            self.assertIn("ncbi_email_configured", data)
        else:
            from research_agent.main import health
            response = health()
            self.assertEqual(response["status"], "healthy")
            self.assertIn("ncbi_email_configured", response)

    def test_research_endpoint_empty_query(self):
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "   "})
            self.assertEqual(response.status_code, 400)
            self.assertIn("cannot be empty", response.json()["detail"])
        else:
            from research_agent.main import research
            q = QuestionInput(question="   ")
            with self.assertRaises(HTTPException) as context:
                research(q)
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("cannot be empty", context.exception.detail)

    @patch("research_agent.main.search_pubmed")
    @patch("research_agent.main.search_store_full")
    @patch("research_agent.main.embed_single")
    def test_research_endpoint_no_papers_found(self, mock_embed_single, mock_search_store_full, mock_search):
        mock_embed_single.return_value = np.array([1.0, 0.0])
        mock_search_store_full.return_value = (None, None)
        mock_search.return_value = []
        
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "unobtainable medical query"})
            self.assertEqual(response.status_code, 404)
            self.assertIn("No PubMed articles found matching the term", response.json()["detail"])
        else:
            from research_agent.main import research
            q = QuestionInput(question="unobtainable medical query")
            with self.assertRaises(HTTPException) as context:
                research(q)
            self.assertEqual(context.exception.status_code, 404)
            self.assertIn("No PubMed articles found matching the term", context.exception.detail)

    @patch("research_agent.main.hybrid_rerank")
    @patch("research_agent.main.save_to_store")
    @patch("research_agent.main.embed_texts")
    @patch("research_agent.main.search_pubmed")
    @patch("research_agent.main.search_store_full")
    @patch("research_agent.main.embed_single")
    def test_research_endpoint_cache_miss_success(self, mock_embed_single, mock_search_store_full, mock_search, mock_embed_texts, mock_save_to_store, mock_rank):
        mock_embed_single.return_value = np.array([1.0, 0.0])
        mock_search_store_full.return_value = (None, None)
        
        mock_papers = [
            {"title": "Test Paper", "abstract": "Abstract", "pmid": "1", "authors": ["A B"], "year": "2023"}
        ]
        mock_search.return_value = mock_papers
        mock_embed_texts.return_value = [np.array([1.0, 0.0])]
        mock_save_to_store.return_value = None
        
        mock_rank.return_value = [
            {
                "title": "Test Paper", 
                "abstract": "Abstract", 
                "pmid": "1", 
                "authors": ["A B"], 
                "year": "2023", 
                "score": 0.76,
                "bm25_score": 0.4,
                "semantic_score": 0.9
            }
        ]
        
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "test query"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["question"], "test query")
            self.assertEqual(len(data["papers"]), 1)
            self.assertEqual(data["papers"][0]["pmid"], "1")
            self.assertEqual(data["papers"][0]["score"], 0.76)
            self.assertEqual(data["papers"][0]["bm25_score"], 0.4)
            self.assertEqual(data["papers"][0]["semantic_score"], 0.9)
        else:
            from research_agent.main import research
            q = QuestionInput(question="test query")
            response = research(q)
            self.assertEqual(response.question, "test query")
            self.assertEqual(len(response.papers), 1)
            self.assertEqual(response.papers[0].pmid, "1")
            self.assertEqual(response.papers[0].score, 0.76)
            self.assertEqual(response.papers[0].bm25_score, 0.4)
            self.assertEqual(response.papers[0].semantic_score, 0.9)

    @patch("research_agent.main.hybrid_rerank")
    @patch("research_agent.main.search_pubmed")
    @patch("research_agent.main.search_store_full")
    @patch("research_agent.main.embed_single")
    def test_research_endpoint_cache_hit_success(self, mock_embed_single, mock_search_store_full, mock_search, mock_rank):
        mock_embed_single.return_value = np.array([1.0, 0.0])
        
        # Simulate FAISS cache hit returning candidates + semantic scores
        mock_papers = [
            {
                "title": "Cached Test Paper", 
                "abstract": "Cached Abstract", 
                "pmid": "99", 
                "authors": ["A B"], 
                "year": "2024"
            }
        ]
        mock_search_store_full.return_value = (mock_papers, [0.9])
        
        mock_rank.return_value = [
            {
                "title": "Cached Test Paper", 
                "abstract": "Cached Abstract", 
                "pmid": "99", 
                "authors": ["A B"], 
                "year": "2024", 
                "score": 0.85,
                "bm25_score": 0.5,
                "semantic_score": 0.9
            }
        ]
        
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "cached query"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["question"], "cached query")
            self.assertEqual(len(data["papers"]), 1)
            self.assertEqual(data["papers"][0]["pmid"], "99")
            self.assertEqual(data["papers"][0]["score"], 0.85)
            # Verify PubMed search was NOT called (proving cache hit path)
            mock_search.assert_not_called()
        else:
            from research_agent.main import research
            q = QuestionInput(question="cached query")
            response = research(q)
            self.assertEqual(response.question, "cached query")
            self.assertEqual(len(response.papers), 1)
            self.assertEqual(response.papers[0].pmid, "99")
            self.assertEqual(response.papers[0].score, 0.85)
            mock_search.assert_not_called()

    @patch("research_agent.main.search_pubmed")
    @patch("research_agent.main.search_store_full")
    @patch("research_agent.main.embed_single")
    def test_research_endpoint_pubmed_error(self, mock_embed_single, mock_search_store_full, mock_search):
        mock_embed_single.return_value = np.array([1.0, 0.0])
        mock_search_store_full.return_value = (None, None)
        mock_search.side_effect = RuntimeError("NCBI connection error")
        
        q = QuestionInput(question="error query")
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "error query"})
            self.assertEqual(response.status_code, 503)
            self.assertIn("PubMed service is temporarily unavailable", response.json()["detail"])
        else:
            from research_agent.main import research
            with self.assertRaises(HTTPException) as context:
                research(q)
            self.assertEqual(context.exception.status_code, 503)
            self.assertIn("PubMed service is temporarily unavailable", context.exception.detail)

if __name__ == "__main__":
    unittest.main()
