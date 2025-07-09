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

from doc_parser import DocxParser
from utils import get_paragragh_difflist, AppConfig, EditCategory

import hashlib # I don't think I'd keep this here too long

# for quick testing
LIST_OF_SAMPLE_DOCX = [
    "examples/file-sample_1MB.docx",
    "examples/my_sample_with_comments_2.docx",
    "examples/my_sample_with_comments.docx",
    "examples/sample3.docx",
    "examples/sample-files.com-basic-text.docx"
]
MODEL_CONTRACT_JSON_V1_SAMPLES = [
    "examples/contracts/model_contract_json_v1.json"
]


def main(argv: t.List[str]) -> int:
    sample: str = "examples/my_sample_with_comments_2.docx"
    with open(MODEL_CONTRACT_JSON_V1_SAMPLES[0], "r") as f:
        model_contract_dict_v1 = json.loads(f.read())
    logging.info(model_contract_dict_v1)
    docx_parser: DocxParser = DocxParser()
    contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = docx_parser.get_paragraphs_with_comments(sample)
    logging.info(json.dumps(contract_meta))
    if contract_meta:
        if len(contract_meta) != 0:
            logging.info(f"it's a gundam: {json.dumps(docx_parser.get_clause_revision_dict(contract_meta))}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    main(sys.argv)