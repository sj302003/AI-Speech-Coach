import os
from dotenv import load_dotenv

load_dotenv()


ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DATABASE_URL = os.getenv("DATABASE_URL")