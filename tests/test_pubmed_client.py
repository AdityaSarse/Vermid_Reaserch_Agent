import unittest
from research_agent.pubmed_client import parse_pubmed_records

class TestPubMedClient(unittest.TestCase):
    def test_parse_pubmed_records_normal(self):
        records = {
            "PubmedArticle": [
                {
                    "MedlineCitation": {
                        "PMID": "12345678",
                        "Article": {
                            "ArticleTitle": "Efficacy of Immunotherapy",
                            "Abstract": {
                                "AbstractText": ["Immunotherapy is highly effective.", "Results show improvement."]
                            },
                            "Journal": {
                                "JournalIssue": {
                                    "PubDate": {"Year": "2023"}
                                }
                            },
                            "AuthorList": [
                                {"LastName": "Smith", "ForeName": "John"},
                                {"LastName": "Doe", "ForeName": "Jane"}
                            ]
                        }
                    }
                }
            ]
        }
        papers = parse_pubmed_records(records)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper["pmid"], "12345678")
        self.assertEqual(paper["title"], "Efficacy of Immunotherapy")
        self.assertEqual(paper["abstract"], "Immunotherapy is highly effective. Results show improvement.")
        self.assertEqual(paper["year"], "2023")
        self.assertEqual(paper["authors"], ["Smith John", "Doe Jane"])

    def test_parse_pubmed_records_missing_fields_and_fallbacks(self):
        records = {
            "PubmedArticle": [
                # Article 1: Missing Abstract, MedlineDate fallback, Collective Name author
                {
                    "MedlineCitation": {
                        "PMID": "87654321",
                        "Article": {
                            "ArticleTitle": "Consortium Study",
                            "Journal": {
                                "JournalIssue": {
                                    "PubDate": {"MedlineDate": "2022 Dec-2023 Jan"}
                                }
                            },
                            "AuthorList": [
                                {"CollectiveName": "Oncology Research Group"},
                                {"LastName": "Sarse", "ForeName": "Aditya"}
                            ]
                        }
                    }
                },
                # Article 2: Missing MedlineCitation (should skip without crashing)
                {},
                # Article 3: Missing Article inside MedlineCitation (should skip without crashing)
                {
                    "MedlineCitation": {
                        "PMID": "9999999"
                    }
                }
            ]
        }
        papers = parse_pubmed_records(records)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper["pmid"], "87654321")
        self.assertEqual(paper["title"], "Consortium Study")
        self.assertEqual(paper["abstract"], "")
        self.assertEqual(paper["year"], "2022")  # regex extracted 4 digit year from MedlineDate
        self.assertEqual(paper["authors"], ["Oncology Research Group", "Sarse Aditya"])

    def test_parse_pubmed_records_malformed_xml_types(self):
        records = {
            "PubmedArticle": [
                {
                    "MedlineCitation": {
                        "PMID": "5555555",
                        "Article": {
                            "ArticleTitle": "Malformed types paper",
                            "Abstract": "Unstructured abstract as raw string",
                            "Journal": {
                                "JournalIssue": {
                                    "PubDate": None
                                }
                            },
                            "AuthorList": "Not a list but string"  # Type mismatch
                        }
                    }
                }
            ]
        }
        papers = parse_pubmed_records(records)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper["pmid"], "5555555")
        self.assertEqual(paper["abstract"], "")  # Abstract was string, not dict, so safely ignored or fallback
        self.assertEqual(paper["year"], None)  # PubDate was None
        self.assertEqual(paper["authors"], [])  # AuthorList was not a list

if __name__ == "__main__":
    unittest.main()
