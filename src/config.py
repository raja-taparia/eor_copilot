import os
from dotenv import load_dotenv

# Load environment variables from .env file and overwrite existing values
# (in case a stale OPENAI_API_KEY is exported in the shell)
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# If the host value is the docker service name, but we're running the API on
# the host machine (not inside Docker), it won't resolve.  Convert to
# localhost automatically to avoid confusion.
if QDRANT_HOST == "qdrant":
    if not os.path.exists("/.dockerenv"):
        print("[config] warning: running outside Docker, changing QDRANT_HOST to 127.0.0.1")
        QDRANT_HOST = "127.0.0.1"

if not OPENAI_API_KEY or OPENAI_API_KEY == "":
    raise ValueError("CRITICAL: OPENAI_API_KEY is missing or invalid in the.env file.")