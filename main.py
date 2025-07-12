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
    # get_prompt_body_v2, 
    AppConfig, 
    EditCategory, 
    ParagraphMatch,)
from langchain_core.prompts import PromptTemplate
from ai_agent import DocxAIAgent
from jinja2 import Environment, FileSystemLoader
from revision_analyzer import DocxAnalyzer


import hashlib # I don't think I'd keep this here too long

# for quick testing
LIST_OF_SAMPLE_DOCX = [
    "examples/file-sample_1MB.docx",
    "examples/my_sample_with_comments_2.docx",
    "examples/my_sample_with_comments.docx",
    "examples/sample3.docx",
    "examples/sample-files.com-basic-text.docx",
    "examples/sample_contract.docx",
    "examples/sample_contract_2.docx"
]
MODEL_CONTRACT_JSON_V1_SAMPLES = [
    "examples/contracts/model_contract_json_v1.json"
]


    

async def main(argv: t.List[str]) -> int:
    sample: str = LIST_OF_SAMPLE_DOCX[6]
    model_contract_v1 = MODEL_CONTRACT_JSON_V1_SAMPLES[0]
    revision_module = DocxAnalyzer() 
    print(await revision_module.aget_revision(sample, model_contract_v1))         
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    asyncio.run(main(sys.argv))