from fastapi import FastAPI, UploadFile, Form
from pathlib import Path
import shutil
from chroma import create_collection
from query import query

app = FastAPI()
    
collection = None 

@app.post("/upload/")
async def upload_codebase(file: UploadFile):
    global collection
    zip_path = Path("temp") / file.filename
    with open(zip_path, "wb") as f:
        f.write(await file.read())
    shutil.unpack_archive(str(zip_path), "unzipped")
    collection = create_collection("unzipped")
    return {"status": "indexed"}

@app.post("/query/")
async def search_codebase(query: str = Form(...)):
    if not collection:
        return {"error": "No collection loaded. Please upload codebase first."}
    results = query(collection, query)
    return {"results": results}
