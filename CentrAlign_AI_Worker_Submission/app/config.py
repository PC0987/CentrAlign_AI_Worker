from pathlib import Path
import os

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "local")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
APPROVAL_THRESHOLD = float(os.getenv("APPROVAL_THRESHOLD", "10000"))
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SANDBOX_FILE = str((Path(__file__).resolve().parent.parent / "static" / "company_sandbox.html").resolve())
