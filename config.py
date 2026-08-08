"""
Configuration: Read keys from environment variables / .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads the .env file in the same directory

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DUNE_API_KEY = os.getenv("DUNE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in the .env file")
if not DUNE_API_KEY:
    raise ValueError("Please set DUNE_API_KEY in the .env file")