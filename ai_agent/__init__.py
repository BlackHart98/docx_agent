import typing as t
import logging
from utils import AIModel


from langchain_core.prompts import PromptTemplate



class DocxAIAgent:
    _api_key: str = ""
    _model_name: str = "" 
    
    
    def __init__(self, api_key: str, model_name: str):
        self._api_key = api_key
        self._model_name = model_name


    def get_revision_analysis(self, paragraph_index: int, body: str) -> t.Tuple[int, t.Optional[t.Dict[str, t.Any]]]:
        return paragraph_index, None