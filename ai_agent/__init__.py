import os
import typing as t
import logging
from utils import AIModel
from dotenv import load_dotenv, find_dotenv


from langchain_core.prompts import PromptTemplate

DOT_ENV_PATH = find_dotenv()
load_dotenv(DOT_ENV_PATH)


class DocxAIAgent:
    _api_key: str = ""
    _model_name: str = "" 
    
    
    def __init__(self, api_key_id: str="MISTRAL_AI_KEY", model_name: str=AIModel.MISTRAL_LARGE_LATEST):
        self._api_key = os.getenv(api_key_id)
        self._model_name = model_name


    def get_revision_analysis(self, paragraph_index: int, body: str) -> t.Tuple[int, t.Optional[t.Dict[str, t.Any]]]:
        return paragraph_index, None