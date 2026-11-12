import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://rehouse:dev@localhost:5432/rehouse')
APP_API_KEY = os.getenv('APP_API_KEY', '')
DTK_BASE_URL = os.getenv('DTK_BASE_URL', '').rstrip('/')
DTK_API_KEY = os.getenv('DTK_API_KEY', '')

ENABLE_ONLINE_COLLECTION = os.getenv("ENABLE_ONLINE_COLLECTION", "false").strip().lower() == "true"
RAW_HTML_DIR = os.getenv("RAW_HTML_DIR", "/data/raw-pages")
COLLECTION_MIN_DELAY_SECONDS = max(30, int(os.getenv("COLLECTION_MIN_DELAY_SECONDS", "30")))
