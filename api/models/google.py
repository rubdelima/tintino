from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from dotenv import load_dotenv
import os
from api.schemas.llm import ChatResponse, SubmitImageResponse
from api.utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    logger.error("Chave da API do Gemini não encontrada. Certifique-se de definir a variável de ambiente GEMINI_API_KEY.")
    exit(1)

logger.info("Carregando modelo Gemini 2.5 Flash via Langchain")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
logger.info("Modelo Gemini 2.5 Flash carregado com sucesso.")

new_chat_llm = llm.with_structured_output(ChatResponse)
submit_llm = llm.with_structured_output(SubmitImageResponse)

logger.info("Configurando cliente GenAI com a chave da API do Gemini")
google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
logger.info("Cliente GenAI configurado com sucesso.")