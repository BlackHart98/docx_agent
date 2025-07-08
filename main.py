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


LIST_OF_SAMPLE_DOCX = [
    "examples/file-sample_1MB.docx",
    "examples/my_sample_with_comments_2.docx",
    "examples/my_sample_with_comments.docx",
    "examples/sample3.docx",
    "examples/sample-files.com-basic-text.docx"
]

def main(argv: t.List[str]) -> int:
    sample: str = "examples/my_sample_with_comments_2.docx"
    
    logging.info(json.dumps(DocxParser().get_paragraphs_with_comments(sample)))
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    main(sys.argv)