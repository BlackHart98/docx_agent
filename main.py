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
from utils import get_paragragh_difflist, get_origin_paragraph, AppConfig, EditCategory

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



# My very first approach: Assuming paragraph always appear in other, i.e., no paragraph swap
# so for this I will rely on the order the paragraphs appear, lol not quite sure what I am doing here
def match_paragraphs(
    model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]]
    , contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]]
) -> t.List[t.Dict[str, str]]:
    result = {}
    sorted_model_contract_dict_v1 = sorted(model_contract_dict_v1, key=itemgetter('paragraph_index'), reverse=False)
    sorted_contract_meta = sorted(contract_meta, key=itemgetter('paragraph_index'), reverse=False)
    for idx in range(len(model_contract_dict_v1)):
        if idx > len(contract_meta):
            break
        else:
            result[sorted_model_contract_dict_v1[idx]["paragraph_index"]] = sorted_contract_meta[idx]["paragraph_index"]
    return result
    

def main(argv: t.List[str]) -> int:
    sample: str = LIST_OF_SAMPLE_DOCX[6]
    with open(MODEL_CONTRACT_JSON_V1_SAMPLES[0], "r") as f:
        model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]] = json.loads(f.read())
        f.close()
    docx_parser: DocxParser = DocxParser()
    contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = docx_parser.get_paragraphs_with_comments(sample)
    # logging.info(f"yepa!: {json.dumps(contract_meta)}")
    if contract_meta:
        if len(contract_meta) != 0:
            result = docx_parser.get_clause_revision_dict(contract_meta)
            temp_ = {item["paragraph_index"] : item for item in result}[15]
            logging.info(f"{json.dumps(result)}")
            logging.info(f"{match_paragraphs(model_contract_dict_v1, contract_meta)}")
            pass
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    main(sys.argv)