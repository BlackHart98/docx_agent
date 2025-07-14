import aiohttp
import json
import os
import sys
import typing as t
import logging
import asyncio
from lib import (
    AnalysisResponse,
    SummaryResponse,
    UploadDocxResponse,
    IndexResponse,
    SummaryRequest,
    AnalysisRequest,)
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
import redis.asyncio as aioredis
from bg_tasks import generate_summary, analyze_summary
from config import Config
import hashlib
from utils import get_analysis

from celery import chain

app = FastAPI()


redis_client = aioredis.from_url(Config.REDIS_URL)


@app.get("/api")
async def root():
    response_sample = IndexResponse()
    return response_sample.model_dump()


@app.put("/api/upload_docx")
async def upload_docx(file : UploadFile = File(...)) -> t.Optional[t.Dict[str, t.Any]]:
    """Upload a file and trigger a Celery task to process it. MAX size 20MB"""
    try:
        file_content = await file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        print(file_hash)
        file_id = f"docx_{file_hash}:{len(file_content)}"
        bg = chain(
            generate_summary.s(file_id=file_id, file_name=file.filename, file_hash=file_hash, file_content=file_content),
            analyze_summary.s()).apply_async()
        response_sample = UploadDocxResponse(
            file_id=file_id,
            file_name=file.filename, 
            file_hash=file_hash, 
            message="File upload succeeded!")
        return response_sample.model_dump()
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@app.get("/api/docx")
async def get_revision_summary(summary: SummaryRequest) -> t.Optional[t.Dict[str, t.Any]]:
    # query the database for the file with this id
    response_sample = SummaryResponse()
    return response_sample.model_dump()


@app.get("/api/docx/revision_analysis")
async def get_revision_analysis(analysis_request: AnalysisRequest) -> t.Optional[t.Dict[str, t.Any]]:
    revision_analysis = get_analysis(analysis_request.file_id)
    response_sample = AnalysisResponse()
    # sample: str = LIST_OF_SAMPLE_DOCX[6]
    # model_contract_v1 = MODEL_CONTRACT_JSON_V1_SAMPLES[0]
    # revision = DocxParser().get_revision_summary(model_contract_v1, sample)
    # if revision: 
    #     revision_analyzer = DocxAnalyzer() 
    #     results = await revision_analyzer.aget_revision(revision, base_delay=1)
    return response_sample.model_dump()