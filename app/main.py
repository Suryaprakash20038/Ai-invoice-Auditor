from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from app.ocr import process_document
from app.logic import validate_invoice

app = FastAPI(title="AI-Powered Smart Invoice Auditor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# homepage
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and PDF allowed")

    contents = await file.read()

    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

    try:
        extracted_data = process_document(contents, file.filename)
        result = validate_invoice(extracted_data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))