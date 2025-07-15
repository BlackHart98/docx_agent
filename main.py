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
from utils import get_analysis, _generate_file_id, get_summary, RevisionSummary

from celery import chain

app = FastAPI()


redis_client = aioredis.from_url(Config.REDIS_URL)


@app.get("/api")
async def root():
    response_sample = IndexResponse()
    return response_sample.model_dump()


@app.put("/api/upload_docx")
async def upload_docx(file : UploadFile = File(...)) -> t.Optional[t.Dict[str, t.Any]]:
    """Upload a file and trigger a background task to process it. MAX size 20MB"""
    try:
        file_content = await file.read()
        file_id = _generate_file_id(file_content)
        _ = chain(
            generate_summary.s(file_id=file_id, file_name=file.filename, file_content=file_content),
            analyze_summary.s()).apply_async()
        response_sample = UploadDocxResponse(
            file_id=file_id,
            file_name=file.filename, 
            message="File upload succeeded!")
        return response_sample.model_dump()
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@app.get("/api/docx")
async def get_revision_summary(summary: SummaryRequest) -> t.Optional[t.Dict[str, t.Any]]:
    """Get file summary using the file id"""
    try:
        summary_result = RevisionSummary(**get_summary(summary.file_id))
        if summary_result:
            response_sample = SummaryResponse(
                file_id=summary.file_id
                , summary=summary_result.contract_meta)
            return response_sample.model_dump()
        else:
            return {"message" : "Could not find any file with the file_id!", "file_id" : summary.file_id}
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Summary request failed")
        
        


@app.get("/api/docx/revision_analysis")
async def get_revision_analysis(analysis_request: AnalysisRequest) -> t.Optional[t.Dict[str, t.Any]]:
    analysis_result = get_analysis(analysis_request.file_id)
    response_sample = AnalysisResponse()
    return response_sample.model_dump()