import os
import typing as t
import logging
from utils import AIModel, HTTPErrorMessage, Config, get_asym_sleep_time, clean_up_json
from dotenv import load_dotenv, find_dotenv
from jinja2 import Environment, FileSystemLoader, Template

import time

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel
from config import Config
from httpx import HTTPStatusError
import asyncio

DOT_ENV_PATH = find_dotenv()
load_dotenv(DOT_ENV_PATH)



class DocxAIAgent:
    _api_key: str = ""
    _model_name: str = "" 
    _llm = None
    _system_role = None
    _revision_schema: t.Set[str] = {
        "analysis_summary", 
        "risk_assessment", 
        "recommended_action", 
        "suggested_response"}
        
    def __init__(
        self,
        role_template: Template,
        api_key: str=os.getenv("MISTRAL_AI_KEY"), 
        model_name: str=AIModel.MISTRAL_LARGE_LATEST, 
    ):
        self._api_key = api_key
        self._model_name = model_name
        self._system_role = ("system", role_template.render({}))
        match model_name:
            case AIModel.MISTRAL_LARGE_LATEST:
                self._llm = ChatMistralAI(
                    model=AIModel.MISTRAL_LARGE_LATEST, 
                    mistral_api_key=self._api_key, 
                    temperature=0,)
            case _:
                raise ValueError(f"Unsupported model: {model_name}")

    def get_revision_analysis(
        self, 
        paragraph_index: int, 
        body: str,
        retry_count:int=Config.DEFAULT_RETRY_COUNT,
        base_delay:float=Config.DEFAULT_DELAY_SECONDS,
        lag_max:float=Config.DEFAULT_LAG_MAX_SECONDS,
    ) -> t.Tuple[int, t.Optional[t.Dict[str, t.Any]], str]:
        prompt_template = ChatPromptTemplate.from_messages([
            self._system_role,
            ("user", "{body}")
        ])
        prompt = prompt_template.format(body=body)
        cleaned_response_content = None
        for i in range(retry_count + 1):
            try:
                response = self._llm.invoke(prompt)
                cleaned_response_content: t.Optional[str] = clean_up_json(response.content, self._revision_schema)
                return paragraph_index, cleaned_response_content, body
            except HTTPStatusError as e:
                logging.error(f"Failed to analyse the revision due to {e}.")
                if retry_count <= i: 
                    break
                sleep_time = get_asym_sleep_time(i + 1, base_delay, lag_max)  
                logging.error(f"Sleeping for {sleep_time:.2f}s before retrying…")
                time.sleep(sleep_time)
            except Exception as e:   
                ValueError(f"Failed to analyse the revision due to {e}")
        return paragraph_index, cleaned_response_content, body
    
    
    async def aget_revision_analysis(
        self, 
        paragraph_index: int, 
        body: str,
        retry_count:int=Config.DEFAULT_RETRY_COUNT,
        base_delay:float=Config.DEFAULT_DELAY_SECONDS,
        lag_max:float=Config.DEFAULT_LAG_MAX_SECONDS,
    ) -> t.Tuple[int, t.Optional[t.Dict[str, t.Any]], str]:
        prompt_template = ChatPromptTemplate.from_messages([
            self._system_role,
            ("user", "{body}")
        ])
        prompt = prompt_template.format(body=body)
        cleaned_response_content = None
        for i in range(retry_count + 1):
            try:
                response = await self._llm.ainvoke(prompt)
                cleaned_response_content: t.Optional[str] = clean_up_json(response.content, self._revision_schema)
                logging.info(f"Successfully analyzed revision for paragraph '{paragraph_index}'")
                return paragraph_index, cleaned_response_content, body
            except HTTPStatusError as e:
                logging.error(f"Failed to analyze the revision for paragraph '{paragraph_index}' due to {e}.")
                if retry_count <= i: 
                    break
                sleep_time = get_asym_sleep_time(i + 1, base_delay, lag_max)  
                logging.error(f"Sleeping for {sleep_time:.2f}s before retrying…")
                await asyncio.sleep(sleep_time)
            except Exception as e:   
                logging.error(f"Failed to analyse the revision due to {e}")
                return paragraph_index, None, body
                
        return paragraph_index, cleaned_response_content, body
        