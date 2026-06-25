import unittest
from unittest.mock import patch
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
    def test_research_endpoint_no_papers_found(self, mock_search):
        mock_search.return_value = []
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "unobtainable medical query"})
            self.assertEqual(response.status_code, 404)
            self.assertIn("No PubMed articles found", response.json()["detail"])
        else:
            from research_agent.main import research
            q = QuestionInput(question="unobtainable medical query")
            with self.assertRaises(HTTPException) as context:
                research(q)
            self.assertEqual(context.exception.status_code, 404)
            self.assertIn("No PubMed articles found", context.exception.detail)

    @patch("research_agent.main.rank_papers")
    @patch("research_agent.main.search_pubmed")
    def test_research_endpoint_success(self, mock_search, mock_rank):
        mock_papers = [
            {"title": "Test Paper", "abstract": "Abstract", "pmid": "1", "authors": ["A B"], "year": "2023"}
        ]
        mock_search.return_value = mock_papers
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

    @patch("research_agent.main.search_pubmed")
    def test_research_endpoint_pubmed_error(self, mock_search):
        mock_search.side_effect = RuntimeError("NCBI connection error")
        if HAS_TEST_CLIENT:
            response = client.post("/research", json={"question": "error query"})
            self.assertEqual(response.status_code, 503)
            self.assertIn("PubMed service is temporarily unavailable", response.json()["detail"])
        else:
            from research_agent.main import research
            q = QuestionInput(question="error query")
            with self.assertRaises(HTTPException) as context:
                research(q)
            self.assertEqual(context.exception.status_code, 503)
            self.assertIn("PubMed service is temporarily unavailable", context.exception.detail)

if __name__ == "__main__":
    unittest.main()
