import os
from dotenv import load_dotenv

load_dotenv()

print(os.getenv("LANDINGAI_API_KEY"))
print(os.getenv("GEMINI_API_KEY"))
print(os.getenv("PATHWAY_LICENSE_KEY"))
