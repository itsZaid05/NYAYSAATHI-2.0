import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data"
DATASET_PATH = DATA_PATH

# Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.getenv("LLM_API_KEY","")

# Vector DB Configuration
VECTORSTORE_PATH = DATA_PATH / "vectorstore"
EMBEDDING_CACHE_PATH = DATA_PATH / "embeddings"

# RAG Configuration
TOP_K_RETRIEVAL = 5
RERANK_TOP_K = 3
HYDE_USE = True
HYBRID_WEIGHT = 0.4

# Generation
TEMPERATURE = 0
MAX_TOKENS = 1500
CONFIDENCE_THRESHOLD = 0.7

# Logging
LOG_PATH = PROJECT_ROOT / "logs"
LOG_LEVEL = "INFO"
