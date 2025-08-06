from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from dotenv import load_dotenv
import os
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.utils.logger import get_logger
from api.constraints import config

logger = get_logger(__name__)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    logger.error("Chave da API do Gemini não encontrada. Certifique-se de definir a variável de ambiente GEMINI_API_KEY.")
    exit(1)

gemini_model = config.get("Gemini", {}).get("model","gemini-2.5-flash") # type:ignore

logger.info(f"Carregando modelo {gemini_model} via Langchain")
llm = ChatGoogleGenerativeAI(
    model=gemini_model,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
logger.info(f"Modelo {gemini_model} carregado com sucesso.")

new_chat_llm = llm.with_structured_output(NewChat)
continue_chat_llm = llm.with_structured_output(ContinueChat)
submit_llm = llm.with_structured_output(SubmitImageResponse)
assert_continue_chat_llm = llm.with_structured_output(AssertContinueChat)

logger.info("Configurando cliente GenAI com a chave da API do Gemini")
google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
logger.info("Cliente GenAI configurado com sucesso.")