from pydantic import BaseModel



class Response(BaseModel):
    pass


class Request(BaseModel):
    pass



class AnalysisResponse(Response):
    pass


class SummaryResponse(Response):
    pass