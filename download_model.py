from sentence_transformers import SentenceTransformer

print("Downloading PubMed-BERT model...")
model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
print("Done. Model cached locally.")
