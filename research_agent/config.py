import os
from dotenv import load_dotenv

load_dotenv()

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL")
NCBI_API_KEY = os.getenv("NCBI_API_KEY")
TOP_K = int(os.getenv("TOP_K", 5))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 20))