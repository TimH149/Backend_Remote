from pathlib import Path
import io
import time

import soundfile as sf
import numpy as np
import json

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
import torch
import torchaudio
from hyperpyyaml import load_hyperpyyaml
from transformers import BitsAndBytesConfig, pipeline

app = FastAPI()

class SentenceRequest(BaseModel):
    sentence: str

# Lets cuDNN pick the fastest conv algorithms for your fixed input shape (30s mel)
torch.backends.cudnn.benchmark = True

# --- Model loading (runs once at startup) ---
# device = torch.device("cpu")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

print("Model laden...")
config_path = Path(__file__).resolve().parent / "1986" / "hyperparams.yaml"
with config_path.open(encoding="utf-8") as f:
    hparams = load_hyperpyyaml(f)

checkpointer = hparams["checkpointer"]
checkpointer.recover_if_possible()

whisper = hparams["whisper"]
valid_search = hparams["valid_search"]

whisper = whisper.to(device)

if device.type == "cuda":
    whisper.model.half()
else:
    whisper.model.float()

whisper.eval()

tokenizer = whisper.tokenizer
model_dtype = next(whisper.parameters()).dtype



def transcribe_signal(signal: torch.Tensor) -> str:
    """signal: shape (1, num_samples), 16kHz, mono, on `device`."""
    wav_lens = torch.tensor([1.0], device=device)
    with torch.inference_mode():
        mel = whisper._get_mel(signal)
        mel = mel.to(model_dtype)
        enc_out = whisper.forward_encoder(mel)
        hyps, *_ = valid_search(enc_out, wav_lens)
    if torch.is_tensor(hyps):
        hyps = hyps.cpu()
    return tokenizer.batch_decode(hyps, skip_special_tokens=True)[0]



async def transcribe(file: UploadFile):
    start = time.time()

    audio_bytes = await file.read()
    print(f"Ontvangen bestand: {file.filename}, grootte: {len(audio_bytes)} bytes")

    # Read straight from memory — no temp file, no disk round trip
    data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    signal = torch.from_numpy(data).unsqueeze(0)

    if sr != 16000:
        signal = torchaudio.transforms.Resample(sr, 16000)(signal)

    signal = signal.to(device)

    text = transcribe_signal(signal)

    duration = time.time() - start
    print(f"Transcriptie klaar in {duration:.2f}s: {text}")

    return {"text": text, "language": "nl", "processing_time": duration}