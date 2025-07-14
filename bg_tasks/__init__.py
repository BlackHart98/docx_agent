from celery import Celery
from config import Config
import json
import os
import sys
import typing as t
import logging
import asyncio
from lib import DocxAnalyzer
from lib import DocxParser
import io

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

celery_app = Celery()

celery_app.config_from_object("config")



@celery_app.task
def generate_summary(
    file_id: str, 
    file_name: str, 
    file_hash: str, 
    file_content: bytes
) -> None: 
    try:
        zip_file_content = io.BytesIO(file_content)
        result = DocxParser().get_revision_summary_bytes(zip_file_content)
        summary_json = result.model_dump_json()
        print("attempting to")
        _commit_summary_to_db()
        return None
    except Exception as e:
        """rollback potential changes"""
        raise




def _commit_summary_to_db() -> None:
    pass