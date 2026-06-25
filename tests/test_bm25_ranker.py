import unittest
from unittest.mock import patch
from research_agent.bm25_ranker import tokenize, rank_papers

class TestBM25Ranker(unittest.TestCase):
    def test_tokenize_basic(self):
        text = "Hello, World! BM25 tokenization check."
        expected = ["hello", "world", "bm25", "tokenization", "check"]
        self.assertEqual(tokenize(text), expected)

    def test_tokenize_empty(self):
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize(None), [])

    def test_tokenize_html(self):
        text = "This is a <i>structured</i> abstract with <b>HTML</b> tags."
        expected = ["this", "is", "a", "structured", "abstract", "with", "html", "tags"]
        self.assertEqual(tokenize(text), expected)

    @patch("research_agent.bm25_ranker.score_papers_semantic")
    def test_rank_papers_normal(self, mock_score_semantic):
        # Mock semantic score returns papers with a semantic_score
        def mock_semantic(question, papers):
            for p in papers:
                p["semantic_score"] = 0.9 if p["pmid"] == "1" else 0.1
            return papers
        mock_score_semantic.side_effect = mock_semantic

        papers = [
            {"title": "Lung cancer efficacy", "abstract": "Study on immunotherapy and lung cancer.", "pmid": "1"},
            {"title": "Diabetes study", "abstract": "Insulin treatment for type 2 diabetes.", "pmid": "2"},
            {"title": "Heart disease study", "abstract": "Cardiovascular health and exercise.", "pmid": "3"},
        ]
        # Rank by term "immunotherapy"
        ranked = rank_papers("immunotherapy", papers)
        self.assertEqual(len(ranked), 3)
        # The lung cancer paper should rank higher
        self.assertEqual(ranked[0]["pmid"], "1")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])
        # Check that individual scores are present
        self.assertIn("bm25_score", ranked[0])
        self.assertIn("semantic_score", ranked[0])

    def test_rank_papers_empty_papers(self):
        self.assertEqual(rank_papers("cancer", []), [])

    @patch("research_agent.bm25_ranker.score_papers_semantic")
    def test_rank_papers_empty_query(self, mock_score_semantic):
        # Mock semantic score returns papers with a semantic_score
        def mock_semantic(question, papers):
            for p in papers:
                p["semantic_score"] = 0.5
            return papers
        mock_score_semantic.side_effect = mock_semantic

        papers = [
            {"title": "Paper 1", "abstract": "Abstract 1", "pmid": "1"},
            {"title": "Paper 2", "abstract": "Abstract 2", "pmid": "2"},
        ]
        # Query with only punctuation
        ranked = rank_papers("??? !!!", papers)
        self.assertEqual(len(ranked), 2)
        # BM25 scores are 0, max defaults to 1.0 -> norm_bm25 = 0.0
        # Semantic scores are 0.5, max is 0.5 -> norm_sem = 1.0
        # Score = 0.4 * 0.0 + 0.6 * 1.0 = 0.6
        self.assertEqual(ranked[0]["score"], 0.6)
        self.assertEqual(ranked[1]["score"], 0.6)

if __name__ == "__main__":
    unittest.main()
