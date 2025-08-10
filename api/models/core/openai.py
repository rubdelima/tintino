
from api.schemas.llm import NewChat, ContinueChat, SubmitImageResponse, AssertContinueChat
from api.utils.logger import get_logger
from api.constraints import config
from api.models.core.interface import CoreModelInterface
from typing import Literal

logger = get_logger(__name__)
load_dotenv()

class OpenAIModel(CoreModelInterface):
    def __init__(self):
        pass
    
    def get_model_name(self, source: Literal["new_chat", "continue_chat", "submit", "assert_continue_chat"]) -> str:
        pass
    
    def new_chat(self, child_name:str, instruction:str) ->NewChat:
        pass
    
    def continue_chat(self) -> ContinueChat:
        pass

    def submit(self) -> SubmitImageResponse:
        pass

    def assert_continue_chat(self) -> AssertContinueChat:
        pass