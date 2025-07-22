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
    AnalysisRequest,
    ParagraphAnalysis,)
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
import redis.asyncio as aioredis
from bg_tasks import generate_summary, analyze_summary
from config import Config
import hashlib
from utils import get_analysis, _generate_file_id, get_summary, RevisionSummary, flattened_analysis

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


@app.get("/api/docx/{file_id}")
async def get_revision_summary(file_id: str) -> t.Optional[t.Dict[str, t.Any]]:
    """Get file summary using the file id"""
    try:
        summary_result = RevisionSummary(**get_summary(file_id))
        if summary_result:
            response_sample = SummaryResponse(
                file_id=file_id, 
                summary=summary_result.contract_meta)
            return response_sample.model_dump()
        else:
            return {"message" : "Could not find any file with the file_id!", "file_id" : file_id}
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Summary request failed")
        
        


@app.get("/api/docx/revision_analysis/{file_id}")
async def get_revision_analysis(file_id: str) -> t.Optional[t.Dict[str, t.Any]]:
    """Get file analysis using the file id"""
    try:
        analysis_result = get_analysis(file_id)
        flattened_analysis_result = flattened_analysis(analysis_result)
        paragraph_analysis_list = [ParagraphAnalysis(**item) for item in flattened_analysis_result]
        if analysis_result:
            response_sample = AnalysisResponse(
                file_id=file_id, 
                paragraph_analyses=paragraph_analysis_list)
            return response_sample.model_dump()
        else:
            return {"message" : "Could not find any file with the file_id!", "file_id" : file_id}
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Analysis request failed")