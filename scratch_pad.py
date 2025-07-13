import json
import os
import sys
import typing as t
import logging
import asyncio
from lib import DocxAnalyzer
from lib import DocxParser


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


    

async def main(argv: t.List[str]) -> int:
    sample: str = LIST_OF_SAMPLE_DOCX[6]
    model_contract_v1 = MODEL_CONTRACT_JSON_V1_SAMPLES[0]
    revision = DocxParser().get_revision_summary(model_contract_v1, sample)
    if revision: 
        revision_analyzer = DocxAnalyzer() 
        results = await revision_analyzer.aget_revision(revision, base_delay=1)
        with open("my_revision.json", "w") as f:
            f.write(json.dumps(results, indent=4))
            f.close()
         
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    asyncio.run(main(sys.argv))