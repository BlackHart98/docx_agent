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
from utils import get_paragragh_difflist, extract_text_content, AppConfig, EditCategory


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
                if len(paragraph.text) != 0:
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
                _, chunk_list = get_paragragh_difflist(item)
                origin_paragraph = "".join([x[0] for x in chunk_list if x[1] != EditCategory.INSERTION])
                paragraph = "".join([x[0] for x in chunk_list if x[1] != EditCategory.DELETION])
                result += [{
                    "paragraph" : paragraph,
                    "uuid" : f"{AppConfig.CLAUSE_HASH_PREFIX}:{hashlib.md5(origin_paragraph.encode()).hexdigest()}",
                    "paragraph_index" : item["paragraph_index"],
                }]
            elif len(item["track_changes"]) != 0:
                _, chunk_list = get_paragragh_difflist(item)
                origin_paragraph = "".join([x[0] for x in chunk_list if x[1] != EditCategory.INSERTION])
                paragraph = "".join([x[0] for x in chunk_list if x[1] != EditCategory.DELETION])
                result += [{
                    "paragraph" : paragraph,
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