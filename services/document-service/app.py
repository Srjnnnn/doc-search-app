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

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/upload-documents")
async def upload_documents(files: list[UploadFile] = File(...)):
    print("Received files for processing:", [file.filename for file in files])
    """Upload and process documents"""
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temporary directory created at: {temp_dir}")
        
        # Ensure the temporary directory exists
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        logger.info(f"Processing {len(files)} files in temporary directory: {temp_dir}")
        print(f"Processing {len(files)} files in temporary directory: {temp_dir}")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # Check if the directory is empty
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files to process")
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
            logger.error(f"Error processing documents: {e}")
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