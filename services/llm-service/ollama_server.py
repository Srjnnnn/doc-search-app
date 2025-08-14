# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import ollama
# from typing import List, Dict, Any
# import logging
# import os
# import requests

# # Configure logging from environment
# log_level = os.getenv("LOG_LEVEL", "INFO")
# log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logging.basicConfig(level=getattr(logging, log_level), format=log_format)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Ollama LLM Service")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize Ollama with Phi4:latest model for Mac Silicon
# MODEL_NAME = "Phi4:latest"
# REQUEST_TIMEOUT = 30
# base_url = f"http://localhost:11434"
# try:
#     llm = "Sercan"
#     logger.info(f"Successfully loaded model: {MODEL_NAME}")
# except Exception as e:
#     logger.error(f"Failed to load model: {e}")
#     llm = None

# @app.post("/generate")
# async def generate_response(request: Dict[str, Any]):
#     """Generate response using Ollama"""
#     # if llm is None:
#     #     raise HTTPException(status_code=503, detail="Model not loaded")
    
#     try:
#         context = request.get("context", "")
#         query = request.get("query", "")
#         max_tokens = request.get("max_tokens", int(os.getenv("DEFAULT_MAX_TOKENS", "512")))
#         temperature = request.get("temperature", float(os.getenv("DEFAULT_TEMPERATURE", "0.7")))
        
#         # Construct prompt with context
#         if context:
#             prompt = f"""Based on the following context, please answer the question.

# Context:
# {context}

# Question: {query}

# Answer:"""
#         else:
#             prompt = f"Question: {query}\n\nAnswer:"
        
#         # # Set sampling parameters
#         # sampling_params = SamplingParams(
#         #     temperature=temperature,
#         #     max_tokens=max_tokens,
#         #     top_p=0.9,
#         #     stop=["Question:", "\n\n"]
#         # )
        
#         # Generate response
#         outputs = ollama.chat(model=MODEL_NAME, 
#                               messages=[{'role': 'system','content': f'You are an expert assistant. Use the following context to answer the user\'s question.\n\nContext:\n{context}',},{"role": "user", "content": prompt}],
#                               temperature=temperature,
#                               max_tokens=max_tokens)
        
#         if not outputs or not outputs[0].outputs:
#             raise HTTPException(status_code=500, detail="No response generated")
#         response = outputs['message']['content']
        
#         return {
#             "response": response,
#             "model": MODEL_NAME,
#             "tokens_generated": len(response.split()),
#             "temperature": temperature,
#             "max_tokens": max_tokens
#         }
        
#     except Exception as e:
#         logger.error(f"Error generating response: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy" if llm is not None else "unhealthy",
#         "model": MODEL_NAME
#     }

# @app.get("/model-info")
# async def get_model_info():
#     """Get detailed model information"""
#     return {
#         "model_name": MODEL_NAME,
#         "model_loaded": llm is not None
#     }

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.getenv("LLM_SERVICE_PORT", "8002"))
#     host = os.getenv("LLM_SERVICE_HOST", "0.0.0.0")
#     uvicorn.run(app, host=host, port=port)