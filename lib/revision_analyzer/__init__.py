import json
import typing as t
import logging
import asyncio

from lib.doc_parser import DocxParser
from utils import (
    get_prompt_body,
    AppConfig, 
    ParagraphMatch,
    RevisionSummary,)
from lib.ai_agent import DocxAIAgent
from jinja2 import Environment, FileSystemLoader, Template

# This class is redundant
class DocxAnalyzer:
    _environment: t.Optional[Environment] = None 
    _prompt_template: t.Optional[Template] = None
    _role_template: t.Optional[Template] = None
    _ai_agent: t.Optional[Environment] = None
    
    
    def __init__(self):
        self._environment = Environment(loader=FileSystemLoader(AppConfig.TEMPLATE_PATH))
        self._prompt_template = self._environment.get_template(AppConfig.PROMPT_TEMPLATE_FILE)
        self._role_template = self._environment.get_template(AppConfig.ROLE_TEMPLATE_FILE)
        self._ai_agent: DocxAIAgent = DocxAIAgent(self._role_template)

        
    async def aget_revision(
        self, 
        revision_summary: RevisionSummary,
        retry_count:int=AppConfig.DEFAULT_RETRY_COUNT,
        base_delay:float=AppConfig.DEFAULT_DELAY_SECONDS,
        lag_max:float=AppConfig.DEFAULT_LAG_MAX_SECONDS
    ) -> t.List[t.Dict[str, t.Any]]:
        contract_meta: t.List[t.Dict[str, t.Any]] = revision_summary.contract_meta
        result_analysis_list = []
        if contract_meta:
            if len(contract_meta) != 0:
                result_analysis_dict = {}
                match_list: t.List[ParagraphMatch] = revision_summary.match_list
                filtered_contract_meta = [item for item in contract_meta if len(item["comments"]) > 0 or len(item["track_changes"]) > 0]
                paragraph_to_body = {}
                match_indexed_by_new_idx = {item.new_paragraph[0] : item.origin_paragraph[2] for item in match_list}
                match_dict = {item.new_paragraph[0] : item for item in match_list}
                for item in filtered_contract_meta:
                    paragraph_to_body[item["paragraph_index"]] = get_prompt_body(item, match_indexed_by_new_idx, self._prompt_template)
                analyze_paragraphs:t.List[t.Any] = [self._ai_agent.aget_revision_analysis(
                    idx, 
                    paragraph_to_body[idx], 
                    base_delay=base_delay, 
                    retry_count=retry_count, 
                    lag_max=lag_max) for idx in paragraph_to_body]
                result_tuple_list: t.List[t.Tuple[int, str, str]] = await asyncio.gather(*analyze_paragraphs)
                result_analysis_dict = {index : revision_analysis for index, revision_analysis, _ in result_tuple_list if revision_analysis}
                result_analysis_list = [{
                    "paragraph_index":index, 
                    "revision_analysis":result_analysis_dict[index],
                    "uuid": match_dict[index].new_paragraph[1],} for index in result_analysis_dict]
        
        return result_analysis_list