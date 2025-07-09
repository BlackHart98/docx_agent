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
from doc_parser import DocxParser
from utils import get_paragragh_difflist, AppConfig

import hashlib # I don't think I'd keep this here too long

# for quick testing
LIST_OF_SAMPLE_DOCX = [
    "examples/file-sample_1MB.docx",
    "examples/my_sample_with_comments_2.docx",
    "examples/my_sample_with_comments.docx",
    "examples/sample3.docx",
    "examples/sample-files.com-basic-text.docx"
]


class DummyModelContract:
    # first draft
    def create_fake_clause_dict(self, contract_meta: t.List[t.Dict[str, t.Any]]) -> t.List[t.Dict[str, t.Any]]:
        result: t.List[t.Dict[str, t.Any]] = []
        for item in contract_meta:
            if item["paragraph"] != "" and len(item["track_changes"]) != 0:
                _, chunk_list = get_paragragh_difflist(item)
                origin_paragraph = "".join([x[0] for x in chunk_list if x[1] != "insert"])
                result += [{
                    "paragraph" : origin_paragraph,
                    "uuid" : f"{AppConfig.CLAUSE_HASH_PREFIX}:{hashlib.md5(origin_paragraph.encode()).hexdigest()}",
                    "paragraph_index" : item["paragraph_index"],
                }]
            elif item["paragraph"] != "":
                result += [{
                    "paragraph" : item["paragraph"],
                    "uuid" : f"{AppConfig.CLAUSE_HASH_PREFIX}:{hashlib.md5(item['paragraph'].encode()).hexdigest()}",
                    "paragraph_index" : item["paragraph_index"],
                }]
            else:
                continue
        return result


def main(argv: t.List[str]) -> int:
    sample: str = "examples/my_sample_with_comments_2.docx"
    docx_parser: DocxParser = DocxParser()
    dummy_model_contract: DummyModelContract = DummyModelContract()
    contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = docx_parser.get_paragraphs_with_comments(sample)
    logging.info(json.dumps(contract_meta))
    if contract_meta:
        if len(contract_meta) != 0:
            model_contract_dict_v1: DummyModelContract = dummy_model_contract.create_fake_clause_dict(contract_meta)
            logging.info(f"{json.dumps(model_contract_dict_v1)}")
            
            logging.info(f"DummyModelContract {json.dumps(docx_parser.get_clause_revision_dict(contract_meta))}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    main(sys.argv)