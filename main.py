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
import langchain as lc
from operator import itemgetter

from doc_parser import DocxParser
from utils import get_paragragh_difflist, get_origin_paragraph, match_paragraphs, AppConfig, EditCategory, ParagraphMatch

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

    

def main(argv: t.List[str]) -> int:
    sample: str = LIST_OF_SAMPLE_DOCX[6]
    with open(MODEL_CONTRACT_JSON_V1_SAMPLES[0], "r") as f:
        model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]] = json.loads(f.read())
        f.close()
    docx_parser: DocxParser = DocxParser()
    contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = docx_parser.get_paragraphs_with_comments(sample)
    if contract_meta:
        if len(contract_meta) != 0:
            result = docx_parser.get_clause_revision_dict(contract_meta)
            temp_ = {item["paragraph_index"] : item for item in result}[15]
            # logging.info(f"{json.dumps(result)}")
            match_list: t.List[ParagraphMatch] = match_paragraphs(model_contract_dict_v1, result)
            logging.info(f"{match_list[0].origin_paragraph}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    main(sys.argv)