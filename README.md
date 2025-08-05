# 🔍 Document Understanding & Web Search Application

A comprehensive AI-powered application that combines document understanding with web search capabilities. Built with modern microservices architecture, this system can answer questions from uploaded documents or search the web when no relevant documents are available.

## ✨ Features

### 📄 Document Understanding

- **LlamaIndex Integration**: Advanced document processing and indexing
- **BGE Embeddings**: High-quality text embeddings using BAAI/bge-large-en-v1.5
- **Milvus Vector Database**: Efficient vector storage and similarity search
- **Binary Quantization**: 32x storage reduction with Hamming distance search
- **Multiple Formats**: Support for PDF, DOC, DOCX, TXT, and Markdown files

### 🌐 Web Search

- **Bing Search API**: Professional web search integration
- **MCP Protocol**: Model Context Protocol for AI assistant compatibility
- **Intelligent Routing**: Automatically switches between document and web search
- **Real-time Results**: Fast and accurate web search results

### 🤖 AI Language Model

- **VLLM Backend**: High-performance inference engine
- **Qwen-3 30B Model**: State-of-the-art multilingual language model
- **GPU Acceleration**: Optimized for NVIDIA GPUs
- **Configurable Parameters**: Adjustable temperature, max tokens, etc.

### 🎨 Modern Frontend

- **React 18**: Modern UI with hooks and functional components
- **Material-UI**: Professional design system
- **Real-time Updates**: Live status and progress indicators
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│  API Gateway    │────│ Document Service│
│   (React)       │    │   (FastAPI)     │    │   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Web Search     │    │     Milvus      │
                       │   Service       │    │  Vector Database│
                       │   Port: 8003    │    │   Port: 19530   │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Bing MCP       │    │   etcd + minio  │
                       │    Server       │    │   (Dependencies)│
                       │   Port: 8080    │    └─────────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   LLM Service   │
                       │     (VLLM)      │
                       │   Port: 8002    │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**: Latest versions
- **NVIDIA GPU**: For LLM inference (optional, can run on CPU)
- **Python 3.10+**: For validation scripts
- **API Keys**: Bing Search API and HuggingFace token

### 1. Clone and Setup

```bash
# Clone the repository
git clone git@github.com:Srjnnnn/doc-search-app.git
cd doc-search-app
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required Environment Variables:**

```bash
# API Keys (Required)
BING_API_KEY=your_bing_search_api_key_here
HUGGINGFACE_TOKEN=hf_your_huggingface_token_here

# GPU Configuration (Optional)
CUDA_VISIBLE_DEVICES=0
GPU_MEMORY_UTILIZATION=0.8
TENSOR_PARALLEL_SIZE=1
```

### 3. Get API Keys

#### Bing Search API Key

1. Visit [Azure Portal](https://portal.azure.com/)
2. Create or sign in to your Azure account
3. Create a new "Bing Search" resource
4. Navigate to "Keys and Endpoint" section
5. Copy your API key

#### HuggingFace Token

1. Visit [HuggingFace](https://huggingface.co/)
2. Sign up/login and go to Settings → Access Tokens
3. Create a new token with read permissions
4. Copy the token (starts with `hf_`)

### 4. Validate and Start

```bash
# Validate environment configuration
python scripts/validate-env.py

# Start all services
make start
# or
docker compose up --build
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 📖 Usage Guide

### Document Upload and Processing

1. **Navigate to "Upload Documents" tab**
2. **Drag and drop files** or click to select (PDF, DOC, DOCX, TXT, MD)
3. **Click "Upload & Process"** to index documents
4. **Wait for processing** - documents are chunked and embedded

### Asking Questions

1. **Go to "Ask Questions" tab**
2. **Type your question** in the text area
3. **Configure options**:
   - ✅ Search uploaded documents
   - ✅ Search the web (fallback)
   - 🌡️ Temperature (creativity level)
   - 📏 Max tokens (response length)
4. **Click "Ask Question"** and wait for response

### Understanding Results

- **Answer**: AI-generated response based on context
- **Sources**: Relevant document chunks or web results
- **Confidence**: System confidence in the answer
- **Method**: Whether answer came from documents or web search

## ⚙️ Configuration

### Environment Variables

| Variable                 | Description              | Default                            | Required |
| ------------------------ | ------------------------ | ---------------------------------- | -------- |
| `BING_API_KEY`           | Bing Search API key      | -                                  | ✅       |
| `HUGGINGFACE_TOKEN`      | HuggingFace access token | -                                  | ✅       |
| `CUDA_VISIBLE_DEVICES`   | GPU devices to use       | `0`                                | ❌       |
| `GPU_MEMORY_UTILIZATION` | VRAM usage ratio         | `0.8`                              | ❌       |
| `TENSOR_PARALLEL_SIZE`   | Multi-GPU parallelism    | `1`                                | ❌       |
| `MAX_MODEL_LEN`          | Context window size      | `4096`                             | ❌       |
| `EMBEDDING_MODEL_NAME`   | Embedding model          | `BAAI/bge-large-en-v1.5`           | ❌       |
| `LLM_MODEL_NAME`         | Language model           | `Qwen/Qwen3-30B-A3B-Instruct-2507` | ❌       |
| `CHUNK_SIZE`             | Document chunk size      | `1000`                             | ❌       |
| `DEFAULT_TOP_K`          | Search result count      | `5`                                | ❌       |

### Performance Tuning

#### For High-End GPUs (24GB+ VRAM)

```bash
GPU_MEMORY_UTILIZATION=0.9
TENSOR_PARALLEL_SIZE=1
MAX_MODEL_LEN=8192
BATCH_SIZE=64
```

#### For Multiple GPUs

```bash
CUDA_VISIBLE_DEVICES=0,1
TENSOR_PARALLEL_SIZE=2
GPU_MEMORY_UTILIZATION=0.8
```

#### For CPU-Only (Limited functionality)

```bash
# Remove GPU requirements from docker-compose.yml
# Use smaller models or disable LLM service
```

## 🛠️ Development

### Makefile Commands

```bash
make help              # Show all available commands
make setup             # Initial project setup
make validate          # Validate environment
make start             # Start all services
make start-detached    # Start in background
make stop              # Stop all services
make clean             # Clean up containers and volumes
make logs              # Show logs from all services
make build             # Build all services
make test              # Run health checks
make restart           # Restart all services
```

### Service Development

#### Hot Reload Development

```bash
# Start with development overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Individual Service Testing

```bash
# Test document service
curl -f http://localhost:8001/health

# Test LLM service
curl -f http://localhost:8002/health

# Test web search service
curl -f http://localhost:8003/health

# Test Bing MCP server
curl -f http://localhost:8080/health
```

#### Logs and Debugging

```bash
# Follow logs for specific service
docker compose logs -f document-service

# Check service status
docker compose ps

# Inspect service
docker compose exec document-service bash
```

## 🚀 Deployment

### Beam Cloud Deployment

1. **Configure deployment environment**:

```bash
cp .env.production .env
# Edit with production values
```

2. **Deploy to Beam Cloud**:

```bash
cd beam-deploy
export BEAM_REGISTRY_URL=your-registry.com
python deploy.py
```

### Manual Deployment

1. **Build and push images**:

```bash
# Tag images for your registry
docker compose build
docker tag doc-search-app_frontend your-registry/frontend:latest
# ... tag other services

# Push to registry
docker push your-registry/frontend:latest
# ... push other services
```

2. **Deploy with Kubernetes**:

```bash
kubectl apply -f beam-deploy/beam.yaml
```

## 🔧 Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
docker --version
docker compose version

# Validate environment
python scripts/validate-env.py

# Check logs
docker compose logs
```

#### GPU Not Detected

```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8-runtime-ubuntu20.04 nvidia-smi

# Update docker-compose.yml if needed
```

#### Out of Memory Errors

```bash
# Reduce GPU memory utilization
GPU_MEMORY_UTILIZATION=0.6

# Use smaller model
LLM_MODEL_NAME=Qwen/Qwen2-7B-Instruct

# Reduce context window
MAX_MODEL_LEN=2048
```

#### Slow Performance

```bash
# Enable GPU if available
CUDA_VISIBLE_DEVICES=0

# Increase batch sizes
BATCH_SIZE=64

# Use multiple GPUs
TENSOR_PARALLEL_SIZE=2
```

### Service-Specific Issues

#### Document Service

- **Milvus connection issues**: Check if Milvus is healthy
- **Embedding model download**: Ensure HuggingFace token is valid
- **File upload failures**: Check file format and size limits

#### LLM Service

- **Model loading failures**: Verify HuggingFace token and model name
- **CUDA errors**: Check GPU availability and memory
- **Slow inference**: Adjust batch size and memory utilization

#### Web Search Service

- **API key errors**: Verify Bing API key is valid and has quota
- **Connection timeouts**: Check internet connectivity
- **Rate limiting**: Implement backoff strategies

## 📊 Monitoring

### Health Checks

```bash
# Overall system health
curl http://localhost:8000/health

# Individual service health
curl http://localhost:8001/health  # Document service
curl http://localhost:8002/health  # LLM service
curl http://localhost:8003/health  # Web search service
curl http://localhost:8080/health  # Bing MCP server
```

### Performance Metrics

- **Response times**: Monitor API response latencies
- **GPU utilization**: Track VRAM and compute usage
- **Search accuracy**: Monitor confidence scores
- **Error rates**: Track failed requests and retries

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **JavaScript**: Follow ESLint rules, use Prettier
- **Docker**: Use multi-stage builds, minimize layers
- **Documentation**: Update README for any new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LlamaIndex**: Document processing and indexing
- **Milvus**: Vector database technology
- **VLLM**: High-performance LLM inference
- **Qwen**: Advanced language model from Alibaba
- **BGE**: Embedding model from BAAI
- **Bing Search MCP**: Based on [leehanchung/bing-search-mcp](https://github.com/leehanchung/bing-search-mcp)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Srjnnnn/doc-search-app/issues)

---

**Made with ❤️ for the AI community**
