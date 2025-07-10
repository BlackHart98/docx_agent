import os
import typing as t
import logging
from utils import AIModel, PromptBodyTemplate
from dotenv import load_dotenv, find_dotenv


from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel

DOT_ENV_PATH = find_dotenv()
load_dotenv(DOT_ENV_PATH)



# BaseChatModel


class DocxAIAgent:
    _api_key: str = ""
    _model_name: str = "" 
    _llm = None
    _system_role = None

    def __init__(
        self, 
        api_key: str=os.getenv("MISTRAL_AI_KEY"), 
        model_name: str=AIModel.MISTRAL_LARGE_LATEST, 
        role: str=PromptBodyTemplate.AI_ROLE_TEMPLATE
    ):
        self._api_key = api_key
        self._model_name = model_name
        self._system_role = ("system", role)
        match model_name:
            case AIModel.MISTRAL_LARGE_LATEST:
                self._llm = ChatMistralAI(
                    model=AIModel.MISTRAL_LARGE_LATEST, 
                    mistral_api_key=self._api_key, 
                    temperature=0,)
            case _:
                logging.error("Model {model_name} not unsopported")
                raise
        


    def get_revision_analysis(
        self, 
        paragraph_index: int, 
        body: str
    ) -> t.Tuple[int, t.Optional[t.Dict[str, t.Any]]]:
        prompt_template = ChatPromptTemplate.from_messages([
            self._system_role,
            ("user", "{body}")
        ])
        prompt = prompt_template.format(body=body)
        print(prompt_template.format(body=body))
        print("::::::::::::::::::::::::::::")
        print(self._llm.invoke(prompt).content)
        return paragraph_index, None