import aiohttp
import json
import os
import sys
import typing as t
import logging
import asyncio
from lib.revision_analyzer import DocxAnalyzer
from lib.doc_parser import DocxParser
from fastapi import FastAPI


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


app = FastAPI()


@app.get("/api")
async def root():
    return {"message" : "My API home"}


@app.post("/api/upload_docx")
async def root():
    return {"message" : "My API index"}


@app.get("/api/revision_analysis/{file_id}")
async def get_revision_summary():
    # sample: str = LIST_OF_SAMPLE_DOCX[6]
    # model_contract_v1 = MODEL_CONTRACT_JSON_V1_SAMPLES[0]
    # revision = DocxParser().get_revision_summary(model_contract_v1, sample)
    # if revision: 
    #     revision_analyzer = DocxAnalyzer() 
    #     results = await revision_analyzer.aget_revision(revision, base_delay=1)
    return {"message": ""}