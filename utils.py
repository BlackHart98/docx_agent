import json
from enum import Enum
import random
import typing as t
import logging
from operator import itemgetter
from dataclasses import dataclass
from langchain_mistralai import ChatMistralAI
from jinja2 import Environment, FileSystemLoader, Template
from config import Config, DATABASE_URL
from pydantic import BaseModel

import hashlib

class EditCategory:
    INSERTION = "insertion"
    DELETION = "deletion"
    ORIGIN = "origin"


class HTTPErrorMessage:
    SERVICE_EXCEEDED_ERROR = "429"



@dataclass
class ParagraphMatch:
    origin_paragraph: t.Optional[t.Tuple[int, str, str]]
    new_paragraph: t.Optional[t.Tuple[int, str, str]]


# list of supported ai models, I just need it form enums lol
class AIModel:
    OPENAI_GPT_4 = ""
    MISTRAL_LARGE_LATEST = "mistral-large-latest"

# @dataclass
class RevisionSummary(BaseModel):
    contract_meta : t.List[t.Dict[str, t.Any]]
    revision: t.List[t.Dict[str, t.Any]]
    match_list: t.List[ParagraphMatch]
    model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]]


def get_prompt_body(paragraph_meta: t.Dict[str, t.Any], match_indexed_by_new_idx: t.Dict[int, str], template: Template) -> str:
    origin_clause = match_indexed_by_new_idx[paragraph_meta["paragraph_index"]]
    result = {
        "origin_clause" : origin_clause,
        "new_clause" : paragraph_meta["paragraph"],
        "track_changes" : paragraph_meta["track_changes"],
        "comments" : paragraph_meta["comments"], 
    }
    return template.render(result)
    

# this is a simplisitic diffing to help me regenerate the original text (deprecated)
def get_paragragh_difflist(paragraph_meta: t.Dict[str, t.Any]) -> t.Optional[t.Tuple[int, t.List[t.Tuple[str, str]]]]:
    if len(paragraph_meta["track_changes"]) != 0:
        sorted_track_change_list: t.List[t.Tuple[int, int, str, str]] = sorted([
            (track_changes["start"], track_changes["end"], track_changes["text"], track_changes["type"]) 
            for track_changes in paragraph_meta["track_changes"]])
        concat_chunk = []
        found_paragraph_start: bool = False
        last_index: int = 0
        for chunk in sorted_track_change_list:
            if chunk[0] != 0 and not found_paragraph_start:
                if chunk[3] == EditCategory.DELETION:
                    concat_chunk += [(paragraph_meta["paragraph"][last_index:], EditCategory.ORIGIN), (chunk[2], chunk[3])]
                else:
                    concat_chunk += [(paragraph_meta["paragraph"], EditCategory.ORIGIN), (chunk[2], chunk[3])]
                found_paragraph_start = True
                last_index = chunk[1]
            elif chunk[0] == 0 and not found_paragraph_start:
                concat_chunk += [(chunk[2], chunk[3])]
                last_index = chunk[1] 
            elif last_index > chunk[1]:
                if chunk[3] == EditCategory.DELETION:
                    concat_chunk += [(paragraph_meta["paragraph"][last_index:], EditCategory.ORIGIN), (chunk[2], chunk[3])]
                else:
                    concat_chunk += [(paragraph_meta["paragraph"], EditCategory.ORIGIN), (chunk[2], chunk[3])]
                last_index = chunk[1]
            else:
                concat_chunk += [(chunk[2], chunk[3])]
                last_index = chunk[1]
        # print(concat_chunk)
        return paragraph_meta["paragraph_index"], concat_chunk
    else:
        return None
    

# this variant applies the changes to the file to recreate the previous paragraph
def get_origin_paragraph(paragraph_meta: t.Dict[str, t.Any]) -> t.Optional[t.Tuple[int, str]]:
    if len(paragraph_meta["track_changes"]) != 0:
        sorted_track_change_list: t.List[t.Tuple[int, int, str, str]] = sorted([
            (track_changes["date"], track_changes["start"], track_changes["end"], track_changes["text"], track_changes["type"]) 
            for track_changes in paragraph_meta["track_changes"]], reverse=True)
        origin_paragraph = paragraph_meta["paragraph"]
        end = len(origin_paragraph) 
        for chunk in sorted_track_change_list:
            if chunk[1] <= 0 and chunk[4] == EditCategory.DELETION:
                origin_paragraph = chunk[3] + origin_paragraph
            elif chunk[1] <= 0 and chunk[4] == EditCategory.INSERTION:
                origin_paragraph = origin_paragraph[chunk[2]:]
            elif chunk[1] >= end and chunk[4] == EditCategory.DELETION:
                 origin_paragraph = origin_paragraph + chunk[3]
            elif (chunk[1] > 0 and chunk[1] < end) and chunk[4] == EditCategory.DELETION:
                origin_paragraph = origin_paragraph[:chunk[1]] + chunk[3] + origin_paragraph[chunk[1]:]
            elif (chunk[1] > 0 and chunk[1] < end) and chunk[4] == EditCategory.INSERTION:
                origin_paragraph = origin_paragraph[chunk[1]:] + chunk[3] + origin_paragraph[:chunk[1]]
        return paragraph_meta["paragraph_index"], origin_paragraph
    else: 
        return paragraph_meta["paragraph_index"], paragraph_meta["paragraph"]


def extract_text_content(elem, tag_suffix, namespaces=Config.DOCX_SCHEMA):
    return "".join(elem.xpath(f'.//w:{tag_suffix}/text()', namespaces=namespaces))




# My very first approach: Assuming paragraph always appear in order, i.e., no paragraph swap or removal
# so for this I will rely on the order the paragraphs appear, lol not quite sure what I am doing here
def match_paragraphs(
    model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]], 
    contract_meta: t.Optional[t.List[t.Dict[str, t.Any]]]
) -> t.List[ParagraphMatch]:
    result = []
    sorted_model_contract_dict_v1 = sorted(model_contract_dict_v1, key=itemgetter('paragraph_index'), reverse=False)
    sorted_contract_meta = sorted(contract_meta, key=itemgetter('paragraph_index'), reverse=False)
    for idx in range(len(model_contract_dict_v1)):
        if idx >= len(contract_meta):
            break
        else:
            result += [ParagraphMatch(
                origin_paragraph=(
                    sorted_model_contract_dict_v1[idx]["paragraph_index"], 
                    sorted_model_contract_dict_v1[idx]["uuid"], 
                    sorted_model_contract_dict_v1[idx]["paragraph"],), 
                new_paragraph=(
                    sorted_contract_meta[idx]["paragraph_index"], 
                    sorted_contract_meta[idx]["uuid"],
                    sorted_contract_meta[idx]["paragraph"],))]
            
    return result


def get_asym_sleep_time(attempt, base_delay, lag_max) -> float:
    lag_rnd = random.uniform(0, lag_max)
    return (base_delay * (2 ** (attempt - 1))) + lag_rnd


def clean_up_json(dirty_json_response: str, revision_schema: t.Set[str]) -> t.Optional[str]:
    removed_ticks = dirty_json_response.strip("`")
    json_prefix: str = "json"
    result = removed_ticks
    for x in json_prefix:
        result = result.strip(x)
    try:
        result_dict = json.loads(result)
        if type(result_dict) == type(dict()):
            if len(revision_schema) != len(result_dict): return None
            for item in result_dict:
                if item not in revision_schema:
                    return None
            return result_dict
    except:
        return None
    return None



def _generate_file_id(file_content: str):
    file_hash: str = hashlib.md5(file_content).hexdigest()
    return f"docx_{file_hash}:{len(file_content)}"



from sqlalchemy import create_engine, text


def fetch_summary_by_file_id(file_id) -> t.List[t.Any]:
    result = []
    try:
        with open(Config.SQL_FILES + "queries/get_summary_by_file_id.sql",  "r") as f:
            sql = text(f.read())
        engine = create_engine(DATABASE_URL, echo=True)
        with engine.connect() as conn:
            result_ = conn.execute(sql, {
                "file_id": file_id,
            })
            result = result_.fetchall()
        return result
    except Exception as e:
        logging.error(f"Failed to get the revision due to {e}")
        return result


def fetch_analysis_by_file_id(file_id) -> t.List[t.Any]:
    result = []
    try:
        with open(Config.SQL_FILES + "queries/get_analysis_by_file_id.sql",  "r") as f:
            sql = text(f.read())
        engine = create_engine(DATABASE_URL, echo=True)
        with engine.connect() as conn:
            result_ = conn.execute(sql, {
                "file_id": file_id,
            })
            result = result_.fetchall()
        return result
    except Exception as e:
        logging.error(f"Failed to get the revision due to {e}")
        return result


def commit_summary_to_db(file_id: str, file_name: str, summary_json: str):
    if len(fetch_summary_by_file_id(file_id)) <= 0:
        with open(Config.SQL_FILES + "insert_into_contract_versions.sql",  "r") as f:
            sql = text(f.read())
        engine = create_engine(DATABASE_URL, echo=True)
        with engine.connect() as conn:
            conn.execute(sql, {
                "file_id": file_id,
                "file_name": file_name,
                "summary_json" : summary_json
            })
            conn.commit()
    else:
        pass


def commit_analysis_to_db(file_id: str, file_name: str, analysis_json: str):
    if len(fetch_analysis_by_file_id(file_id)) <= 0:
        with open(Config.SQL_FILES + "insert_into_analysis_table.sql",  "r") as f:
            sql = text(f.read())
        engine = create_engine(DATABASE_URL, echo=True)
        with engine.connect() as conn:
            conn.execute(sql, {
                "file_id": file_id,
                "analysis_json" : analysis_json
            })
            conn.commit()
    else:
        pass


def get_summary(file_id: str) -> t.Optional[t.Dict[str, t.Any]]:
    result = fetch_summary_by_file_id(file_id)
    if result:
        _, _, summary_json, _, _, _ = result[0]
        summary = json.loads(summary_json)
        return summary
    else:
        return None


def get_analysis(file_id: str) -> t.Optional[t.List[t.Dict[str, t.Any]]]:
    result = fetch_analysis_by_file_id(file_id)
    if result:
        _, _, analysis_json, _= result[0]
        analysis_json = json.loads(analysis_json)
        return analysis_json
    else:
        return None


def flattened_analysis(analysis_result: t.Optional[t.List[t.Dict[str, t.Any]]]) -> t.List[t.Dict[str, t.Any]]:
    result = []
    for item in analysis_result:
        new_item = {}
        for key in item:
            if key != "revision_analysis":
                new_item[key] = item[key]
            else:
                for sub_key in item["revision_analysis"]:
                    new_item[sub_key] = item["revision_analysis"][sub_key]
        result += [new_item]
    return result