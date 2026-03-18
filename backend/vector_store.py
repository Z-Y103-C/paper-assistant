import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
import os

# 禁用 ChromaDB 遥测
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """向量数据库管理器"""

    def __init__(self, persist_directory: str, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model

        # 初始化ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 初始化嵌入模型 - 使用国内镜像
        logger.info(f"Loading embedding model: {embedding_model}")
        # 设置环境变量以使用 HuggingFace 镜像
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        self.embedding_model = SentenceTransformer(embedding_model)
        
        self.collection = None
    
    def create_collection(self, collection_name: str = "papers"):
        """创建或获取集合"""
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{collection_name}' ready")
            return self.collection
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    def add_documents(self, chunks: List[Dict], collection_name: str = "papers"):
        """添加文档块到向量数据库"""
        if not self.collection:
            self.create_collection(collection_name)
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk['content'])
            metadatas.append(chunk.get('metadata', {}))
            ids.append(chunk['metadata'].get('chunk_id', str(len(ids))))
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(chunks)} chunks to vector database")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def search(self, query: str, n_results: int = 5, collection_name: str = "papers") -> List[Dict]:
        """搜索相关文档块"""
        if not self.collection:
            self.create_collection(collection_name)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    search_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else 0
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def search_by_metadata(self, metadata_filter: Dict, n_results: int = 10, collection_name: str = "papers") -> List[Dict]:
        """根据元数据过滤搜索"""
        if not self.collection:
            self.create_collection(collection_name)
        
        try:
            results = self.collection.get(
                where=metadata_filter,
                limit=n_results
            )
            
            search_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    search_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][i] if results.get('metadatas') else {}
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            return []
    
    def delete_document(self, document_id: str, collection_name: str = "papers"):
        """删除指定文档的所有块"""
        if not self.collection:
            self.create_collection(collection_name)
        
        try:
            # 先查找所有相关块
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def get_collection_stats(self, collection_name: str = "papers") -> Dict:
        """获取集合统计信息"""
        if not self.collection:
            self.create_collection(collection_name)
        
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': collection_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}
    
    def clear_collection(self, collection_name: str = "papers"):
        """清空集合"""
        try:
            self.client.delete_collection(name=collection_name)
            self.collection = None
            logger.info(f"Cleared collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False
