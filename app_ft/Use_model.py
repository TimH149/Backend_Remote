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

print("Fietje laden...")
fietje_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)
fietje = pipeline(
    "text-generation",
    model="BramVanroy/fietje-2b-chat",
    model_kwargs={
        "quantization_config": fietje_config,
        "attn_implementation": "sdpa",
    },
    device_map="cuda" if device.type == "cuda" else "auto",
)
print("Fietje geladen.")

def original_correct_with_fietje(sentence: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "Je bent een Nederlandse grammaticacorrector.",
        },
        {
            "role": "user",
            "content": f"""Corrigeer deze Nederlandse zin zonder de betekenis te veranderen of onnodig te herschrijven.
Leg daarna kort in het Nederlands uit wat er fout was.

Gebruik exact dit formaat:
{{
    "is_correct": <boolean of de zin grammaticaal correct is>,
    "verbeterde_zin": "<gecorrigeerde Nederlandse zin.>",
    "feedback": "<Korte uitleg.>"
}}

Originele zin:
{sentence}""",
        },
    ]

    output = fietje(messages, max_new_tokens=128, do_sample=False)
    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1]["content"].strip()
    return generated.strip()

def run_with_fietje(sentence: str) -> str:
    messages = [
    {
        "role": "User",
        "content": f"""
    Je bent een nauwkeurige Nederlandse grammaticacorrector.

    Je taak is om één Nederlandse zin te controleren.

    Regels:
    - Controleer grammatica, spelling, woordvolgorde, vervoegingen, lidwoorden en interpunctie.
    - Verander de betekenis van de zin niet.
    - Herschrijf de zin niet puur om hem mooier of natuurlijker te maken.
    - Corrigeer alleen objectieve taal- of grammaticafouten.
    - Als de originele zin correct is, moet `verbeterde_zin` exact gelijk zijn aan de originele zin.
    - `is_correct` is alleen `true` als er geen correcties nodig zijn.
    - Geef bij `feedback` een korte uitleg over verbeterde grammatica.
    - Geef uitsluitend geldige JSON terug.
    - Gebruik geen Markdown, codeblokken of tekst buiten het JSON-object.

    Gebruik exact deze structuur:

    {{
        "is_correct": <boolean>,
        "verbeterde_zin": "<De gecontroleerde zin.>",
        "feedback": "<Korte uitleg.>"
    }}

    Controleer deze zin:
    {sentence}
    """
        }
    ]

    output = fietje(messages, max_new_tokens=128, do_sample=False)
    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1]["content"].strip()
    return generated.strip()

def chat_suggestion_fietje(sentence: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Je bent een Nederlandse grammaticacorrector. "
                "Antwoord altijd uitsluitend met geldig JSON. "
                "Gebruik geen Markdown en geen tekst buiten het JSON-object."
            ),
        },
        {
            "role": "user",
            "content": f"""
Corrigeer deze Nederlandse zin alleen als dat nodig is (de zinnen zijn altijd in tegenwoordige tijd bedoeld).

Zin:
{sentence}

Antwoord exact in deze vorm:
{{
  "verbeterde_zin": "..."
  "is_zin_correct": <true of false>
}}
""",
        },
    ]

    output = fietje(
        messages,
        max_new_tokens=128,
        do_sample=False,
    )

    generated = output[0]["generated_text"]

    if isinstance(generated, list):
        response = generated[-1]["content"].strip()
    else:
        response = generated.strip()

    print("FIETJE RESPONSE:", repr(response))

    return response

def fietje_1(sentence: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Je bent een Nederlandse grammaticacorrector. "
                "Antwoord altijd uitsluitend met geldig JSON. "
                "Gebruik geen Markdown en geen tekst buiten het JSON-object."
            ),
        },
        {
            "role": "user",
            "content": f"""
Geef feedback over de grammatica van deze zin.

Zin:
{sentence}

Antwoord exact in deze vorm:
{{
  "grammaticale_feedback": "..."
  "is_de_zin_correct": <true of false>
}}
""",
        },
    ]

    output = fietje(
        messages,
        max_new_tokens=128,
        do_sample=False,
    )

    generated = output[0]["generated_text"]

    if isinstance(generated, list):
        response = generated[-1]["content"].strip()
    else:
        response = generated.strip()

    print("FIETJE RESPONSE:", repr(response))

    return response

def correct_with_fietje(sentence: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "Je bent een Nederlandse grammaticacorrector.",
        },
        {
            "role": "user",
            "content": f"""Corrigeer deze Nederlandse zin zonder de betekenis te veranderen of onnodig te herschrijven. Als de zin all correct is, stuur dan de originele zin terug.

Gebruik exact dit formaat (JSON):
{{
    "verbeterde_zin": "<gecorrigeerde Nederlandse zin>",
    "is_zin_correct": <true of false afhankelijk van of de zin correct was>
}}

Originele zin:
{sentence}""",
        },
    ]
    output = fietje(messages, max_new_tokens=128, do_sample=False)
    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1]["content"].strip()
    return generated.strip()

    # output = fietje(messages, max_new_tokens=128, do_sample=False)
    # generated = output[0]["generated_text"]
    # if isinstance(generated, list):
    #     return generated[-1]["content"].strip()
    # return generated.strip()

def explain_mistakes_with_fietje(originalSentence: str, improved) -> str:
    messages = [
        {
            "role": "system",
            "content": "Je bent een Nederlandse grammaticacorrector.",
        },
        {
            "role": "user",
            "content": f"""
Als deze zinnen anders zijn, kan je kort uitleg geven over wat er verbeterd was?

Als de zin correct is, kan je dan sturen: de zin was correct.

Gebruik exact dit formaat:

<Feedback over de zin>

Originele zin:
{originalSentence}

Verbeterde zin:
{improved}
""",
        },
    ]

    output = fietje(messages, max_new_tokens=128, do_sample=False)
    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1]["content"].strip()
    return generated.strip()


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


# --- Warmup: run one dummy inference now, so the FIRST real request
# doesn't pay for CUDA kernel compilation / cuDNN autotune / lazy inits ---
print("Warming up model...")
_warmup_signal = torch.zeros(1, 16000 * 5, device=device)  # 5s of silence
_ = transcribe_signal(_warmup_signal)
print("Model geladen, server is ready.")


@app.post("/transcribe")
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


@app.post("/correct")
async def correct_sentence(request: SentenceRequest):
    sentence = request.sentence.strip()

    try:
        fietje_response = fietje_1(sentence)

        print(fietje_response)
        result = json.loads(fietje_response)

        print(result)

        feedback = result["grammaticale_feedback"]
        # feedback = result["feedback"]
        is_correct = result["is_de_zin_correct"]

    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return {
            "errors": [ 
                {
                    "type": "inputValidation",
                    "message": f"{exc}",
                    "modelResponse": f"{fietje_response}"
                }
            ]
        }
        

    return {
        "data": {
            "originalSentence": sentence,
            "explanation": feedback,
            "isCorrect": is_correct,
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}