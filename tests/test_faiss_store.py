import unittest
import os
import shutil
import numpy as np
from research_agent import faiss_store

class TestFaissStore(unittest.TestCase):
    def setUp(self):
        # Redirect store paths to test paths
        self.original_index_path = faiss_store.INDEX_PATH
        self.original_metadata_path = faiss_store.METADATA_PATH
        
        faiss_store.INDEX_PATH = "test_faiss_store/index.faiss"
        faiss_store.METADATA_PATH = "test_faiss_store/metadata.json"
        
        # Cleanup clean directory
        if os.path.exists("test_faiss_store"):
            shutil.rmtree("test_faiss_store")

    def tearDown(self):
        # Restore original paths
        faiss_store.INDEX_PATH = self.original_index_path
        faiss_store.METADATA_PATH = self.original_metadata_path
        
        # Cleanup
        if os.path.exists("test_faiss_store"):
            shutil.rmtree("test_faiss_store")

    def test_save_and_search_store(self):
        # 1. Test search on empty/non-existent store returns None
        res_empty = faiss_store.search_store(np.zeros(768))
        self.assertIsNone(res_empty)

        # 2. Save some papers
        papers = [
            {"pmid": "1", "title": "Paper 1", "abstract": "Abstract 1"},
            {"pmid": "2", "title": "Paper 2", "abstract": "Abstract 2"},
        ]
        # Vectors where paper 1 is [1.0, 0.0, ...] and paper 2 is [0.0, 1.0, ...]
        embeddings = np.zeros((2, 768))
        embeddings[0, 0] = 1.0
        embeddings[1, 1] = 1.0

        faiss_store.save_to_store(embeddings, papers)

        # Verify files were created
        self.assertTrue(os.path.exists(faiss_store.INDEX_PATH))
        self.assertTrue(os.path.exists(faiss_store.METADATA_PATH))

        # 3. Search store with a query aligned with Paper 1
        query_embedding = np.zeros(768)
        query_embedding[0] = 1.0

        results = faiss_store.search_store(query_embedding, top_k=2)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)
        # Paper 1 (pmid "1") should be first because it is perfectly aligned
        self.assertEqual(results[0]["pmid"], "1")
        self.assertGreater(results[0]["score"], results[1]["score"])

        # 4. Save duplicate paper (pmid "1") and check it is ignored
        more_papers = [
            {"pmid": "1", "title": "Paper 1 Duplicate", "abstract": "Abstract 1"},
            {"pmid": "3", "title": "Paper 3", "abstract": "Abstract 3"},
        ]
        more_embeddings = np.zeros((2, 768))
        more_embeddings[0, 0] = 1.0
        more_embeddings[1, 2] = 1.0

        faiss_store.save_to_store(more_embeddings, more_papers)
        
        # Verify store has exactly 3 papers (no duplicates added)
        all_results = faiss_store.search_store(query_embedding, top_k=5)
        self.assertEqual(len(all_results), 3)

        # 5. Test search_store_full
        res_full, scores = faiss_store.search_store_full(query_embedding, top_k=5)
        self.assertIsNotNone(res_full)
        self.assertEqual(len(res_full), 3)
        self.assertEqual(len(scores), 3)
        self.assertEqual(res_full[0]["pmid"], "1")
        self.assertGreater(scores[0], scores[1])

    def test_search_store_full_empty(self):
        res, scores = faiss_store.search_store_full(np.zeros(768))
        self.assertIsNone(res)
        self.assertIsNone(scores)

if __name__ == "__main__":
    unittest.main()
