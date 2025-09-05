from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from vllm import LLM, SamplingParams
from typing import List, Dict, Any
import logging
import os

# Configure logging from environment
log_level = os.getenv("LOG_LEVEL", "INFO")
log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig(level=getattr(logging, log_level), format=log_format)
logger = logging.getLogger(__name__)

app = FastAPI(title="VLLM LLM Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize VLLM with configuration from environment variables
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen3-30B-A3B-Instruct-2507")
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.8"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "4096"))
TENSOR_PARALLEL_SIZE = int(os.getenv("TENSOR_PARALLEL_SIZE", "1"))

try:
    llm = LLM(
        model=MODEL_NAME,
        tensor_parallel_size=TENSOR_PARALLEL_SIZE,
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        max_model_len=MAX_MODEL_LEN,
        trust_remote_code=True
    )
    logger.info(f"Successfully loaded model: {MODEL_NAME}")
    logger.info(f"GPU Memory Utilization: {GPU_MEMORY_UTILIZATION}")
    logger.info(f"Max Model Length: {MAX_MODEL_LEN}")
    logger.info(f"Tensor Parallel Size: {TENSOR_PARALLEL_SIZE}")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    llm = None

@app.post("/generate")
async def generate_response(request: Dict[str, Any]):
    """Generate response using VLLM"""
    if llm is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        context = request.get("context", "")
        logger.info(f"Context received: {context}")
        query = request.get("query", "")
        max_tokens = request.get("max_tokens", int(os.getenv("DEFAULT_MAX_TOKENS", "512")))
        temperature = request.get("temperature", float(os.getenv("DEFAULT_TEMPERATURE", "0.7")))
        
        # Construct prompt with context
        if context:
            prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
        else:
            prompt = f"Question: {query}\n\nAnswer:"
        
        # Set sampling parameters
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            stop=["Question:", "\n\n"]
        )
        
        # Generate response
        outputs = llm.generate([prompt], sampling_params)
        logger.info(f"Outputs: {outputs}")
        response = outputs[0].outputs[0].text.strip()
        
        return {
            "response": response,
            "model": MODEL_NAME,
            "tokens_generated": len(response.split()),
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if llm is not None else "unhealthy",
        "model": MODEL_NAME,
        "gpu_memory_utilization": GPU_MEMORY_UTILIZATION,
        "max_model_len": MAX_MODEL_LEN,
        "tensor_parallel_size": TENSOR_PARALLEL_SIZE
    }

@app.get("/model-info")
async def get_model_info():
    """Get detailed model information"""
    return {
        "model_name": MODEL_NAME,
        "model_loaded": llm is not None,
        "configuration": {
            "gpu_memory_utilization": GPU_MEMORY_UTILIZATION,
            "max_model_len": MAX_MODEL_LEN,
            "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
            "default_max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "512")),
            "default_temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LLM_SERVICE_PORT", "8002"))
    host = os.getenv("LLM_SERVICE_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)