import os
from dotenv import load_dotenv

load_dotenv()  # carga las variables desde .env
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

from langchain_cohere import ChatCohere

llm = ChatCohere(
    model="command-a-plus-05-2026",
    cohere_api_key=COHERE_API_KEY,
    temperature=0
)