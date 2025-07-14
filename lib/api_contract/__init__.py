from pydantic import BaseModel
from utils import Config
import typing as t
from config import Config


class Response(BaseModel):
    pass

class Job(BaseModel):
    pass

class IndexResponse(Response):
    pass


class SummaryResponse(Response):
    file_id: str
    tracked_changes: t.List[t.Dict[str, t.Any]]


class ParagraphAnalysis(Response):
    paragraph_index: int
    analysis_summary: str
    risk_assessment: str
    recommended_action: str
    suggested_response: str



class AnalysisResponse(Response):
    file_id: str
    paragraph_analyses: t.List[ParagraphAnalysis]


class AnalysisResponse(Response):
    file_id: str
    paragraph_analyses: str


class UploadDocxResponse(Response):
    file_id: str #file_id will be the concatenation of docx_<file_name>:<file_hash>
    file_name: str 
    file_hash: str
    message: str
    
    
    
    

class Request(BaseModel):
    pass


class SummaryRequest(Request):
    file_id: str
    
    
class AnalysisRequest(Request):
    file_id: str