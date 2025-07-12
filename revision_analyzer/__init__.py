import json
import os
import sys
import typing as t
from docx import Document
import zipfile
import logging
from difflib import *
from lxml import etree
import subprocess
import xmlformatter
from docx.oxml.ns import qn
from operator import itemgetter
import asyncio

from doc_parser import DocxParser
from utils import (
    get_paragragh_difflist, 
    get_origin_paragraph, 
    match_paragraphs,
    get_prompt_body,
    AppConfig, 
    EditCategory, 
    ParagraphMatch,)
from langchain_core.prompts import PromptTemplate
from ai_agent import DocxAIAgent
from jinja2 import Environment, FileSystemLoader, Template

# This class is redundant
class DocxAnalyzer:
    _environment: t.Optional[Environment] = None 
    _prompt_template: t.Optional[Template] = None
    _role_template: t.Optional[Template] = None
    _docx_parser: t.Optional[Environment] = None
    _ai_agent: t.Optional[Environment] = None
    
    
    def __init__(self):
        self._environment = Environment(loader=FileSystemLoader(AppConfig.TEMPLATE_PATH))
        self._prompt_template = self._environment.get_template(AppConfig.PROMPT_TEMPLATE_FILE)
        self._role_template = self._environment.get_template(AppConfig.ROLE_TEMPLATE_FILE)
        self._docx_parser: DocxParser = DocxParser()
        self._ai_agent: DocxAIAgent = DocxAIAgent(self._role_template)

    
    def get_revision(self, docx_file_path: str, model_contract_v1_path: str) -> t.List[t.Dict[str, t.Any]]:
        with open(model_contract_v1_path, "r") as f:
            model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]] = json.loads(f.read())
            f.close()
        contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = self._docx_parser.get_paragraphs_with_comments(docx_file_path)
        result_analysis_dict = {}
        if contract_meta:
            if len(contract_meta) != 0:
                result = self._docx_parser.get_clause_revision_dict(contract_meta)
                match_list: t.List[ParagraphMatch] = match_paragraphs(model_contract_dict_v1, result)
                filtered_contract_meta = [item for item in contract_meta if len(item["comments"]) > 0 or len(item["track_changes"]) > 0]
                paragraph_to_body = {}
                match_indexed_by_new_idx = {item.new_paragraph[0] : item.origin_paragraph[2] for item in match_list}
                for item in filtered_contract_meta:
                    paragraph_to_body[item["paragraph_index"]] = get_prompt_body(item, match_indexed_by_new_idx, self._prompt_template)
                
                for idx in paragraph_to_body:
                    index, revision_analysis, _ = self._ai_agent.get_revision_analysis(idx, paragraph_to_body[idx], base_delay=4, retry_count=5)
                    result_analysis_dict[index] = revision_analysis
        return [result_analysis_dict]
    
    
    async def aget_revision(self, docx_file_path: str, model_contract_v1_path: str):
        with open(model_contract_v1_path, "r") as f:
            model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]] = json.loads(f.read())
            f.close()
        contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = self._docx_parser.get_paragraphs_with_comments(docx_file_path)
        result_analysis_dict = {}
        if contract_meta:
            if len(contract_meta) != 0:
                result = self._docx_parser.get_clause_revision_dict(contract_meta)
                match_list: t.List[ParagraphMatch] = match_paragraphs(model_contract_dict_v1, result)
                filtered_contract_meta = [item for item in contract_meta if len(item["comments"]) > 0 or len(item["track_changes"]) > 0]
                paragraph_to_body = {}
                match_indexed_by_new_idx = {item.new_paragraph[0] : item.origin_paragraph[2] for item in match_list}
                for item in filtered_contract_meta:
                    paragraph_to_body[item["paragraph_index"]] = get_prompt_body(item, match_indexed_by_new_idx, self._prompt_template)

                corountine_list:t.List[t.Any] = [self._ai_agent.aget_revision_analysis(idx, paragraph_to_body[idx]) for idx in paragraph_to_body]
                result_tuple_list = await asyncio.gather(*corountine_list, return_exceptions=True)
                result_analysis_dict = {index : revision_analysis for index, revision_analysis, _ in result_tuple_list}
                
        return [result_analysis_dict]