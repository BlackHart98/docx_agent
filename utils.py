import typing as t
import logging
from operator import itemgetter
from dataclasses import dataclass

class AppConfig: # I can't think of a better name
    CLAUSE_HASH_PREFIX = "contract_clause"
    DOCX_SCHEMA = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


class EditCategory:
    INSERTION = "insertion"
    DELETION = "deletion"
    ORIGIN = "origin"



@dataclass
class ParagraphMatch:
    origin_paragraph: t.Optional[t.Tuple[int, str, str]]
    new_paragraph: t.Optional[t.Tuple[int, str, str]]



class PromptBodyTemplate:
    INPUT_PROMPT_TEMPLATE:str = """
original clause:
{}

new clause:
{}

---
changes: 
{}
comments:
{}
"""

    CHANGES_TEMPLATE:str = """
type: {}
date: {}
author: {}
content: {}
___
"""

    COMMENT_TEMPLATE:str = """
date: {}
content: {}
author: {}
___
"""
    AI_ROLE_TEMPLATE: str = """"""


class AIModel:
    OPENAI_GPT_4 = ""
    MISTRAL_LARGE_LATEST = "mistral-large-latest"


def get_prompt_body(paragraph_meta: t.Dict[str, t.Any], match_indexed_by_new_idx: t.Dict[int, str]) -> str:
    origin_clause = match_indexed_by_new_idx[paragraph_meta["paragraph_index"]]
    comments_str: str = ""
    for comment in paragraph_meta["comments"]:
        comments_str += PromptBodyTemplate.COMMENT_TEMPLATE.format(
            comment['type'], 
            comment['content'], 
            comment['author'])
    track_changes_str: str = ""
    for track_change in paragraph_meta["track_changes"]:
        track_changes_str += PromptBodyTemplate.CHANGES_TEMPLATE.format(
            track_change['type'], 
            track_change['date'], 
            track_change['author'], 
            track_change['text'])
    return PromptBodyTemplate.INPUT_PROMPT_TEMPLATE.format(
        origin_clause, 
        paragraph_meta["paragraph"], 
        track_changes_str, 
        comments_str)
        


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


def extract_text_content(elem, tag_suffix, namespaces=AppConfig.DOCX_SCHEMA):
    return "".join(elem.xpath(f'.//w:{tag_suffix}/text()', namespaces=namespaces))




# My very first approach: Assuming paragraph always appear in other, i.e., no paragraph swap
# so for this I will rely on the order the paragraphs appear, lol not quite sure what I am doing here
def match_paragraphs(
    model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]], 
    contract_meta: t.Optional[t.List[t.Dict[str, t.Any]]]
) -> t.List[ParagraphMatch]:
    result = []
    sorted_model_contract_dict_v1 = sorted(model_contract_dict_v1, key=itemgetter('paragraph_index'), reverse=False)
    sorted_contract_meta = sorted(contract_meta, key=itemgetter('paragraph_index'), reverse=False)
    for idx in range(len(model_contract_dict_v1)):
        if idx > len(contract_meta):
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