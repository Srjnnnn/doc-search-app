from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import shutil
from document_processor import DocumentProcessor

app = FastAPI(title="Document Processing Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = DocumentProcessor()

@app.post("/upload-documents")
async def upload_documents(files: list[UploadFile] = File(...)):
    """Upload and process documents"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Save uploaded files
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            
            # Process documents
            result = processor.process_documents(temp_dir)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_documents(query: dict):
    """Search for similar document chunks"""
    try:
        query_text = query.get("query", "")
        top_k = query.get("top_k", 5)
        
        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")
        
        results = processor.search_similar_chunks(query_text, top_k)
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)