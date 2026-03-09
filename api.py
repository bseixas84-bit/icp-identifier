import io
import os

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from engine.analyzer import analyze_customers
from engine.scorer import score_prospects
from engine.models import ICPProfile

load_dotenv()
app = FastAPI(title="ICP Identifier")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory state for the session
_state: dict = {}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    df["churned"] = df["churned"].apply(lambda x: str(x).lower() in ("true", "1", "yes", "sim"))

    icp = analyze_customers(df, api_key)
    _state["icp"] = icp
    _state["customers_df"] = df
    return icp.model_dump()


@app.post("/score")
async def score(file: UploadFile = File(...)):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")
    if "icp" not in _state:
        raise HTTPException(400, "Run /analyze first to generate ICP")

    content = await file.read()
    prospects_df = pd.read_csv(io.BytesIO(content))
    results = score_prospects(_state["icp"], prospects_df, api_key)
    return [r.model_dump() for r in results]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
