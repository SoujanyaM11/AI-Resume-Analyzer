import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.pop("GEMINI_API_KEY", None)   # tests must never depend on (or use) a real key
os.environ.pop("GEMINI_MODEL", None)
