from fastapi import FastAPI, UploadFile

from app.datamodels import GrammarCheckRequest, ContentCheckRequest

app = FastAPI()

@app.post("/transcribe")
async def transcribe(file: UploadFile):
    return {"text": "transcriped text", "language": "nl", "processing_time": 0.5}

@app.post("/grammar-check")
async def grammar_check(request: GrammarCheckRequest):
    return {
                "correct": True,
                "correction": "none",
                "feedback": "Je bent een topper! Goed gedaan."
            }

@app.post("/grammar-check/stage-1")
async def grammar_check_stage_1(request: GrammarCheckRequest):
    return {
                "correct": True,
                "correction": "none",
                "feedback": "Je bent een topper! Goed gedaan."
            }

@app.post("/grammar-check/easy")
async def check_grammar_easy(request: GrammarCheckRequest):
    return {
                "correct": True,
                "feedback": "Je bent een topper! Goed gedaan.",
                "correction": "",
                "mistake_type": None
            }

@app.post("/grammar-check/stage-3")
async def grammar_check_stage_3(request: GrammarCheckRequest):
    return {
                "correct": True,
                "correction": "none",
                "feedback": "Je bent een topper! Goed gedaan."
            }

@app.post("/content-check")
async def content_check(request: ContentCheckRequest):
    return {
        "correct": True
    }

@app.get("/health")
async def health():
    return {"status": "ok"} 