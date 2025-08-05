import os
import logging
from typing import List, Dict, Any
import numpy as np
from llama_index.core import SimpleDirectoryReader, Document
from sentence_transformers import SentenceTransformer
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, milvus_host: str = "milvus", milvus_port: int = 19530):
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        self.collection_name = "document_embeddings"
        self.dimension = 1024  # BGE-large dimension
        
        # Connect to Milvus
        self._connect_milvus()
        self._create_collection()
    
    def _connect_milvus(self):
        """Connect to Milvus vector database"""
        try:
            connections.connect("default", host=self.milvus_host, port=self.milvus_port)
            logger.info("Connected to Milvus successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _create_collection(self):
        """Create Milvus collection for document embeddings"""
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text_hash", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="binary_embedding", dtype=DataType.BINARY_VECTOR, dim=self.dimension)
        ]
        
        schema = CollectionSchema(fields, "Document embeddings collection")
        self.collection = Collection(self.collection_name, schema)
        
        # Create index for binary vectors with Hamming distance
        index_params = {
            "metric_type": "HAMMING",
            "index_type": "BIN_FLAT"
        }
        self.collection.create_index("binary_embedding", index_params)
        logger.info("Created Milvus collection with binary index")
    
    def process_documents(self, directory_path: str) -> Dict[str, Any]:
        """Process documents using LlamaIndex directory reader"""
        try:
            # Use LlamaIndex to read documents
            reader = SimpleDirectoryReader(directory_path)
            documents = reader.load_data()
            
            logger.info(f"Loaded {len(documents)} documents")
            
            # Process and embed documents
            processed_chunks = []
            for doc in documents:
                chunks = self._chunk_document(doc)
                processed_chunks.extend(chunks)
            
            embeddings = self._generate_embeddings(processed_chunks)
            binary_embeddings = self._binarize_embeddings(embeddings)
            
            # Store in Milvus
            self._store_embeddings(processed_chunks, embeddings, binary_embeddings)
            
            return {
                "status": "success",
                "processed_documents": len(documents),
                "total_chunks": len(processed_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return {"status": "error", "message": str(e)}
    
    def _chunk_document(self, document: Document, chunk_size: int = 1000) -> List[str]:
        """Chunk document into smaller pieces"""
        text = document.text
        chunks = []
        
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            if len(chunk.strip()) > 50:  # Filter out very short chunks
                chunks.append(chunk.strip())
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using BGE-large model"""
        embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
        return embeddings
    
    def _binarize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Apply binary quantization to embeddings"""
        # Simple binary quantization: positive -> 1, negative -> 0
        binary_embeddings = (embeddings > 0).astype(np.uint8)
        
        # Pack bits for Milvus binary vector format
        packed_binary = np.packbits(binary_embeddings, axis=1)
        return packed_binary
    
    def _store_embeddings(self, texts: List[str], embeddings: np.ndarray, binary_embeddings: np.ndarray):
        """Store embeddings in Milvus"""
        text_hashes = [hashlib.md5(text.encode()).hexdigest() for text in texts]
        
        entities = [
            text_hashes,
            texts,
            embeddings.tolist(),
            binary_embeddings.tolist()
        ]
        
        self.collection.insert(entities)
        self.collection.flush()
        self.collection.load()
        logger.info(f"Stored {len(texts)} embeddings in Milvus")
    
    def search_similar_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using binary quantization and Hamming distance"""
        try:
            # Generate and binarize query embedding
            query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
            binary_query = self._binarize_embeddings(query_embedding)
            
            # Search in Milvus using binary vectors
            search_params = {"metric_type": "HAMMING", "params": {}}
            
            results = self.collection.search(
                data=binary_query.tolist(),
                anns_field="binary_embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "text_hash"]
            )
            
            similar_chunks = []
            for hits in results:
                for hit in hits:
                    similar_chunks.append({
                        "text": hit.entity.get("text"),
                        "distance": hit.distance,
                        "score": 1 / (1 + hit.distance)  # Convert distance to similarity score
                    })
            
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []