import json
import os
import sys
import typing as t
# from docx import Document
import zipfile
import logging
from difflib import *
from lxml import etree
import subprocess
import xmlformatter
from utils import (
    get_paragragh_difflist, 
    extract_text_content, 
    AppConfig, 
    EditCategory, 
    get_origin_paragraph,
    match_paragraphs, 
    RevisionSummary,
    ParagraphMatch)


import hashlib

class DocxParser:
    def _get_all_comments(
        self,
        docx_zip: zipfile.ZipFile, 
        oo_xmlns: t.Dict[str, str]=AppConfig.DOCX_SCHEMA
    ) -> t.List[t.Dict[str, t.Any]]:
        if 'word/comments.xml' not in [item.filename for item in docx_zip.filelist]: 
            return []
        else:
            comments_xml = docx_zip.read('word/comments.xml')
            et = etree.XML(comments_xml)
            comments = et.xpath('//w:comment',namespaces=oo_xmlns)
            result: t.List[t.Dict[str, t.Any]] = []
            for c in comments:
                comment = c.xpath('string(.)',namespaces=oo_xmlns)
                comment_id = c.xpath('@w:id',namespaces=oo_xmlns)[0]
                comment_author = c.xpath('@w:author',namespaces=oo_xmlns)[0]
                comment_date = c.xpath('@w:date',namespaces=oo_xmlns)[0]
                result += [{
                    "comment" : comment,
                    "comment_id" : comment_id,
                    "comment_author" : comment_author,
                    "comment_date" : comment_date,
                }]
            return result
    
    
    def _get_paragraph_comments(
        self,
        paragraph: t.Any, 
        comments_dict: t.Dict[str, t.Any], 
    ) -> t.Any:
        result = []
        for item in paragraph.iter():
            if item.tag.endswith('commentReference'):
                comment_id = item.get(f'{{{AppConfig.DOCX_SCHEMA["w"]}}}id')
                comment = comments_dict[comment_id]
                result.append(comment)
        return result
    
    
    # TODO: revisit this function
    def _get_comment_positions(
        self, 
        document_xml: t.Any, 
        para_idx: int, 
        oo_xmlns: t.Dict[str, str]=AppConfig.DOCX_SCHEMA
    ) -> t.List[t.Dict[str, t.Any]]:
        tree = etree.fromstring(document_xml)
        paragraphs = tree.findall('.//w:body//w:p', namespaces=AppConfig.DOCX_SCHEMA)
        paragraph = paragraphs[para_idx]
        text_accum = ""
        comment_positions = []
        inside_comment = False
        comment_id = None
        start_offset = None

        for elem in paragraph.iter():
            if elem.tag.endswith('commentRangeStart'):
                inside_comment = True
                comment_id = elem.get(f'{{{oo_xmlns["w"]}}}id')
                start_offset = len(text_accum)
            elif elem.tag.endswith('commentRangeEnd') and inside_comment:
                end_offset = len(text_accum)
                comment_positions.append({
                    'comment_id': comment_id,
                    'start': start_offset,
                    'end': end_offset
                })
                inside_comment = False
                comment_id = None
                start_offset = None
            elif elem.tag.endswith('t'):
                text_accum += elem.text or ""
            else:
                continue
        return comment_positions
    
    # TODO: Revisit this function
    def _get_track_changes(
        self, 
        document_xml: t.Any, 
        para_idx: int, 
    ) -> t.List[t.Dict[str, t.Any]]:
        tree = etree.fromstring(document_xml)
        paragraphs = tree.findall('.//w:body//w:p', namespaces=AppConfig.DOCX_SCHEMA)
        paragraph = paragraphs[para_idx]
        para_text = ""
        changes = []
        cursor = 0
        for child in paragraph:
            if child.tag.endswith("r"):  # normal run
                text = extract_text_content(child, "t")
                para_text += text
                cursor += len(text)
            elif child.tag.endswith("ins"):
                change_type = EditCategory.INSERTION
                author = child.get(f'{{{AppConfig.DOCX_SCHEMA["w"]}}}author')
                date = child.get(f'{{{AppConfig.DOCX_SCHEMA["w"]}}}date')
                change_text = extract_text_content(child, "t")

                start = cursor
                end = cursor + len(change_text)

                changes.append({
                    "type": change_type,
                    "author": author,
                    "date": date,
                    "text": change_text,
                    "start": start,
                    "end": end
                })

                para_text += change_text
                cursor += len(change_text)
            elif child.tag.endswith("del"):
                change_type = EditCategory.DELETION
                author = child.get(f'{{{AppConfig.DOCX_SCHEMA["w"]}}}author')
                date = child.get(f'{{{AppConfig.DOCX_SCHEMA["w"]}}}date')
                change_text = extract_text_content(child, "delText")

                start = cursor
                end = cursor + len(change_text)

                changes.append({
                    "type": change_type,
                    "author": author,
                    "date": date,
                    "text": change_text,
                    "start": start,
                    "end": end
                })

                para_text += change_text  # include in visible text
                cursor += len(change_text)
            else:
                continue   
        return changes

    # TODO: revisit this function
    def _get_paragraphs_with_comments(
        self,
        # document_file_path: str, 
        docx_zip: zipfile.ZipFile,
        comments: t.List[t.Dict[str, t.Any]], 
    ) -> t.List[t.Dict[str, t.Any]]:
        document_xml = docx_zip.read('word/document.xml')
        tree = etree.fromstring(document_xml)
        paragraphs = tree.findall('.//w:body//w:p', namespaces=AppConfig.DOCX_SCHEMA)
        comments_dict = {item["comment_id"] : item for item in comments}
        revisions_to_paragraph = []
        for idx, paragraph in enumerate(paragraphs):
            track_changes: t.List[t.Dict[str, t.Any]] = self._get_track_changes(document_xml, idx)
            paragraph_text = extract_text_content(paragraph, "t", AppConfig.DOCX_SCHEMA)
            if comments_dict:
                comments = self._get_paragraph_comments(paragraph, comments_dict)
                comment_pos = self._get_comment_positions(document_xml, idx)
                revisions_to_paragraph += [{
                        "paragraph" : paragraph_text,
                        "paragraph_index" : idx,
                        "comment_pos": comment_pos,
                        "comments": comments,
                        "track_changes": track_changes,
                    }]
            else:
                if len(extract_text_content(paragraph, "t")) != 0:
                    revisions_to_paragraph += [{
                            "paragraph" : paragraph_text,
                            "paragraph_index" : idx,
                            "comment_pos": [],
                            "comments": [],
                            "track_changes": track_changes,
                        }]
        return revisions_to_paragraph
    
    
    def get_paragraphs_with_comments(self, sample: str) -> t.Optional[t.List[t.Dict[str, t.Any]]]:
        docx_zip = zipfile.ZipFile(sample)
        comments = self._get_all_comments(docx_zip)
        return self._get_paragraphs_with_comments(docx_zip, comments)

    
    def get_clause_revision_dict(self, contract_meta: t.List[t.Dict[str, t.Any]]) -> t.List[t.Dict[str, t.Any]]:
        result = []
        for item in contract_meta:
            if item["paragraph"] != "" and len(item["track_changes"]) != 0:
                _, origin_paragraph = get_origin_paragraph(item)
                result += [{
                    "paragraph" : item["paragraph"],
                    "uuid" : f"{AppConfig.CLAUSE_HASH_PREFIX}:{hashlib.md5(origin_paragraph.encode()).hexdigest()}",
                    "paragraph_index" : item["paragraph_index"],
                }]
            elif len(item["track_changes"]) != 0:
                _, origin_paragraph = get_origin_paragraph(item)
                result += [{
                    "paragraph" : item["paragraph"],
                    "uuid" : f"{AppConfig.CLAUSE_HASH_PREFIX}:{hashlib.md5(origin_paragraph.encode()).hexdigest()}",
                    "paragraph_index" : item["paragraph_index"],
                }]
            elif item["paragraph"] != "":
                result += [{
                    "paragraph" : item["paragraph"],
                    "uuid" : f"{AppConfig.CLAUSE_HASH_PREFIX}:{hashlib.md5(item['paragraph'].encode()).hexdigest()}",
                    "paragraph_index" : item["paragraph_index"],
                }]
        return result
    
    
    def get_revision_summary(self, model_contract_v1_path: str, docx_file_path: str) -> t.Optional[RevisionSummary] :
        with open(model_contract_v1_path, "r") as f:
            model_contract_dict_v1: t.Optional[t.List[t.Dict[str, t.Any]]] = json.loads(f.read())
            f.close()
        contract_meta : t.Optional[t.List[t.Dict[str, t.Any]]] = self.get_paragraphs_with_comments(docx_file_path)
        if contract_meta:
            if len(contract_meta) != 0:
                result = self.get_clause_revision_dict(contract_meta)
                match_list: t.List[ParagraphMatch] = match_paragraphs(model_contract_dict_v1, result)
                return RevisionSummary(contract_meta=contract_meta, revision=result, match_list=match_list, model_contract_dict_v1=model_contract_dict_v1)
        return None
    
    
    
    # result_analysis_dict = {}
    #             result = self._docx_parser.get_clause_revision_dict(contract_meta)
    #             match_list: t.List[ParagraphMatch] = match_paragraphs(model_contract_dict_v1, result)
    #             filtered_contract_meta = [item for item in contract_meta if len(item["comments"]) > 0 or len(item["track_changes"]) > 0]
    #             paragraph_to_body = {}
    #             match_indexed_by_new_idx = {item.new_paragraph[0] : item.origin_paragraph[2] for item in match_list}
    #             match_dict = {item.new_paragraph[0] : item for item in match_list}
    #             for item in filtered_contract_meta:
    #                 paragraph_to_body[item["paragraph_index"]] = get_prompt_body(item, match_indexed_by_new_idx, self._prompt_template)

    #             analyze_paragraphs:t.List[t.Any] = [self._ai_agent.aget_revision_analysis(
    #                 idx, 
    #                 paragraph_to_body[idx], 
    #                 base_delay=base_delay, 
    #                 retry_count=retry_count, 
    #                 lag_max=lag_max) for idx in paragraph_to_body]
    #             result_tuple_list = await asyncio.gather(*analyze_paragraphs)
    #             result_analysis_dict = {index : revision_analysis for index, revision_analysis, _ in result_tuple_list}
    #             result_analysis_list = [{
    #                 "paragraph_index":index, 
    #                 "revision_analysis":result_analysis_dict[index], 
    #                 # "origin_paragraph": match_dict[index].origin_paragraph[2],
    #                 # "new_paragraph": match_dict[index].new_paragraph[2],
    #                 "uuid": match_dict[index].new_paragraph[1],} for index in result_analysis_dict]