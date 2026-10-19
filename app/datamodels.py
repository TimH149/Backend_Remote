from pydantic import BaseModel
from grammar.contentchecker import SentenceRequirement


class GrammarCheckRequest(BaseModel):
    sentence: str


class ContentCheckRequest(BaseModel):
    sentence: str
    requirements: list[SentenceRequirement]