import unittest
from unittest.mock import patch
import numpy as np
from research_agent.embeddings import score_papers_semantic

class TestEmbeddings(unittest.TestCase):
    @patch("research_agent.embeddings.embed_texts")
    def test_score_papers_semantic(self, mock_embed):
        # Mock embedding vectors:
        # Question vector: [1.0, 0.0]
        # Paper 1 vector: [1.0, 0.0] (perfect cosine similarity = 1.0)
        # Paper 2 vector: [0.0, 1.0] (orthogonal cosine similarity = 0.0)
        
        def mock_embed_side_effect(texts):
            if len(texts) == 1:
                return np.array([[1.0, 0.0]])
            else:
                return np.array([[1.0, 0.0], [0.0, 1.0]])
                
        mock_embed.side_effect = mock_embed_side_effect

        papers = [
            {"title": "Paper One", "abstract": "Abstract One", "pmid": "1"},
            {"title": "Paper Two", "abstract": "Abstract Two", "pmid": "2"},
        ]

        scored = score_papers_semantic("test question", papers)
        self.assertEqual(len(scored), 2)
        
        # Paper 1 should have semantic score of 1.0
        self.assertEqual(scored[0]["semantic_score"], 1.0)
        # Paper 2 should have semantic score of 0.0
        self.assertEqual(scored[1]["semantic_score"], 0.0)

if __name__ == "__main__":
    unittest.main()
