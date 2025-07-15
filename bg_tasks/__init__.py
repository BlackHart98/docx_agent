from celery import Celery
from config import Config
import json
import os
import sys
import typing as t
import logging
import asyncio
from lib import DocxAnalyzer, DocxParser, RevisionSummary
import io

from utils import commit_summary_to_db, commit_analysis_to_db

celery_app = Celery()

celery_app.config_from_object("config")



@celery_app.task
def generate_summary(
    file_id: str, 
    file_name: str, 
    # file_hash: str, 
    file_content: bytes
) -> t.Tuple[str, str, str]: 
    try:
        zip_file_content = io.BytesIO(file_content)
        result = DocxParser().get_revision_summary_bytes(zip_file_content)
        summary_json = result.model_dump_json()
        print("attempting to...... commit to summary tables")
        commit_summary_to_db(file_id, file_name, summary_json)
        return file_id, file_name, summary_json
    except Exception as e:
        """rollback potential changes"""
        raise

@celery_app.task
def analyze_summary(input: t.Tuple[str, str, str]) -> None: 
    try:
        file_id, file_name, summary_json = input
        summary_ = RevisionSummary(**json.loads(summary_json))
        # print(summary_)
        results = asyncio.run(DocxAnalyzer().aget_revision(summary_, base_delay=1))
        result_str: str =  json.dumps(results)
        print("attempting to...... commit to revision tables")
        commit_analysis_to_db(file_id, file_name, result_str)
    except Exception as e:
        """rollback potential changes"""
        raise



def _commit_summary_to_db() -> None:
    pass


def _get_summary_by_id_db() -> None:
    pass


def _commit_analysis_to_db() -> None:
    pass