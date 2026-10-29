from fastapi import FastAPI, UploadFile
from faster_whisper import WhisperModel
import tempfile
import time

from grammar.contentchecker import check_content
from app.datamodels import GrammarCheckRequest, ContentCheckRequest
from feedback.Feedback import (
    get_feedback,
    get_stage_one_feedback,
    get_stage_three_feedback,
    get_easy_feedback,
)
import transcription.transcription as transcription

app = FastAPI()

@app.post("/transcribe")
async def transcribe(file: UploadFile):
    return await transcription.transcribe(file)

@app.post("/grammar-check")
async def grammar_check(request: GrammarCheckRequest):
    result = get_feedback(request.sentence)
    print(f"Grammar check result for sentence: {request.sentence.split()} -> {result}")

    return result

@app.post("/grammar-check/stage-1")
async def grammar_check_stage_1(request: GrammarCheckRequest):
    result = get_stage_one_feedback(request.sentence)
    print(f"Grammar check stage 1 result: {result}")

    return result

@app.post("/grammar-check/easy")
async def check_grammar_easy(request: GrammarCheckRequest):
    result = get_easy_feedback(request.sentence)
    print(f"Grammar check easy result: {result}")
    return result
    
@app.post("/grammar-check/stage-3")
async def grammar_check_stage_3(request: GrammarCheckRequest):
    result = get_stage_three_feedback(request.sentence)
    print(f"Grammar check stage 3 result: {result}")

    return result

@app.post("/content-check")
async def content_check(request: ContentCheckRequest):
    print(request)
    correct = check_content(request.sentence.split(), request.requirements)

    print(f"Content check result for sentence: {request.sentence.split()} -> {correct}")

    return {
        "correct": True
    }

@app.get("/health")
async def health():
    return {"status": "ok"} 