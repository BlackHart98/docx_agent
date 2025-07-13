from pydantic import BaseModel
from utils import AppConfig
import typing as t
    


class Response(BaseModel):
    pass


class Request(BaseModel):
    pass

class IndexResponse(Response):
    pass

class AnalysisResponse(Response):
    pass


class SummaryResponse(Response):
    pass


class UploadDocxResponse(Response):
    file_id: str
    message: str = "Upload successful!"