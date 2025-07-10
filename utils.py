import typing as t
import logging
from dataclasses import dataclass

@dataclass
class AppConfig: # I can't think of a better name
    CLAUSE_HASH_PREFIX = "contract_clause"
    DOCX_SCHEMA = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


@dataclass
class EditCategory:
    INSERTION = "insertion"
    DELETION = "deletion"
    ORIGIN = "origin"


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