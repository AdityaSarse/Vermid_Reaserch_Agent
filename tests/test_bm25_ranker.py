import unittest
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

    def test_rank_papers_normal(self):
        papers = [
            {"title": "Lung cancer efficacy", "abstract": "Study on immunotherapy and lung cancer.", "pmid": "1"},
            {"title": "Diabetes study", "abstract": "Insulin treatment for type 2 diabetes.", "pmid": "2"},
            {"title": "Heart disease study", "abstract": "Cardiovascular health and exercise.", "pmid": "3"},
        ]
        # Rank by term "immunotherapy"
        ranked = rank_papers("immunotherapy", papers)
        self.assertEqual(len(ranked), 3)
        # The lung cancer paper should rank higher because it matches "immunotherapy"
        self.assertEqual(ranked[0]["pmid"], "1")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_rank_papers_empty_papers(self):
        self.assertEqual(rank_papers("cancer", []), [])

    def test_rank_papers_empty_query(self):
        papers = [
            {"title": "Paper 1", "abstract": "Abstract 1", "pmid": "1"},
            {"title": "Paper 2", "abstract": "Abstract 2", "pmid": "2"},
        ]
        # Query with only punctuation
        ranked = rank_papers("??? !!!", papers)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["score"], 0.0)
        self.assertEqual(ranked[1]["score"], 0.0)

if __name__ == "__main__":
    unittest.main()
