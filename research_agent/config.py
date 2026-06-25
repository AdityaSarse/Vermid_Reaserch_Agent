import os
from dotenv import load_dotenv

load_dotenv()

ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL")
TOP_K = int(os.getenv("TOP_K", 5))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 20))