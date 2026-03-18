from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import uuid
import logging
from datetime import datetime

from config import config
from document_loader import DocumentLoader
from text_processor import TextProcessor
from vector_store import VectorStore
from deepseek_client import DeepSeekClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 验证配置
try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")
    exit(1)

# 初始化应用
app = FastAPI(title="Paper Assistant API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化核心组件
document_loader = DocumentLoader()
text_processor = TextProcessor(
    chunk_size=config.CHUNK_SIZE,
    chunk_overlap=config.CHUNK_OVERLAP
)
vector_store = VectorStore(
    persist_directory=config.VECTOR_DB_DIR,
    embedding_model=config.EMBEDDING_MODEL
)
deepseek_client = DeepSeekClient(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL
)

# 存储文档元数据
documents_db = {}

# 数据模型
class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None

class SummaryRequest(BaseModel):
    document_id: str

class DeepReadRequest(BaseModel):
    document_id: str

class KnowledgeExpansionRequest(BaseModel):
    document_id: str
    topic: str

class SearchRequest(BaseModel):
    query: str
    n_results: int = 5

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    upload_time: str
    metadata: Dict
    status: str

# API端点

@app.get("/")
async def root():
    return {
        "message": "Paper Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传文档（PDF或DOCX）"""
    try:
        # 检查文件类型
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.docx']:
            raise HTTPException(status_code=400, detail="只支持PDF和DOCX文件")
        
        # 检查文件大小
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > config.MAX_UPLOAD_SIZE * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大{config.MAX_UPLOAD_SIZE}MB）"
            )
        
        # 生成文档ID
        document_id = str(uuid.uuid4())
        
        # 保存文件
        file_path = os.path.join(config.UPLOAD_DIR, f"{document_id}{file_extension}")
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 加载文档
        document_data = document_loader.load_document(file_path)
        
        if not document_data['success']:
            raise HTTPException(status_code=500, detail=f"文档加载失败: {document_data.get('error', '未知错误')}")
        
        # 提取章节
        sections = document_loader.extract_sections(document_data['full_text'])
        
        # 文本分块
        chunks = text_processor.chunk_sections(sections, document_id)
        
        # 添加到向量数据库
        vector_store.add_documents(chunks)
        
        # 存储文档元数据
        documents_db[document_id] = {
            'filename': file.filename,
            'file_type': file_extension,
            'file_path': file_path,
            'upload_time': datetime.now().isoformat(),
            'metadata': document_data['metadata'],
            'sections': sections,
            'chunks_count': len(chunks),
            'status': 'processed'
        }
        
        logger.info(f"Document uploaded successfully: {document_id}")
        
        return DocumentResponse(
            document_id=document_id,
            filename=file.filename,
            file_type=file_extension,
            upload_time=documents_db[document_id]['upload_time'],
            metadata=document_data['metadata'],
            status="processed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传文档时发生错误: {str(e)}")

@app.get("/documents")
async def list_documents():
    """列出所有文档"""
    return {
        "documents": [
            {
                "document_id": doc_id,
                "filename": doc_info['filename'],
                "file_type": doc_info['file_type'],
                "upload_time": doc_info['upload_time'],
                "chunks_count": doc_info['chunks_count'],
                "status": doc_info['status']
            }
            for doc_id, doc_info in documents_db.items()
        ],
        "total": len(documents_db)
    }

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """获取文档详情"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = documents_db[document_id]
    
    return {
        "document_id": document_id,
        "filename": doc_info['filename'],
        "file_type": doc_info['file_type'],
        "upload_time": doc_info['upload_time'],
        "metadata": doc_info['metadata'],
        "chunks_count": doc_info['chunks_count'],
        "status": doc_info['status']
    }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 从向量数据库删除
        vector_store.delete_document(document_id)
        
        # 删除文件
        doc_info = documents_db[document_id]
        if os.path.exists(doc_info['file_path']):
            os.remove(doc_info['file_path'])
        
        # 从内存删除
        del documents_db[document_id]
        
        logger.info(f"Document deleted successfully: {document_id}")
        return {"message": "文档删除成功"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文档时发生错误: {str(e)}")

@app.post("/search")
async def search_documents(request: SearchRequest):
    """搜索文档"""
    try:
        results = vector_store.search(request.query, request.n_results)
        
        return {
            "query": request.query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索文档时发生错误: {str(e)}")

@app.post("/summary")
async def generate_summary(request: SummaryRequest):
    """生成论文摘要"""
    if request.document_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        doc_info = documents_db[request.document_id]
        full_text = ' '.join([section for section in doc_info['sections'].values()])
        
        # 生成摘要
        summary = deepseek_client.generate_summary(full_text)
        
        return {
            "document_id": request.document_id,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成摘要时发生错误: {str(e)}")

@app.post("/question")
async def ask_question(request: QuestionRequest):
    """智能问答"""
    try:
        # 搜索相关内容
        context_results = vector_store.search(request.question, n_results=3)
        
        if not context_results:
            return {
                "answer": "抱歉，我没有找到相关的内容来回答您的问题。请尝试重新表述问题或上传相关文档。",
                "sources": []
            }
        
        # 组合上下文
        context = '\n\n'.join([result['content'] for result in context_results])
        
        # 使用DeepSeek回答问题
        answer = deepseek_client.answer_question(
            request.question,
            context,
            request.conversation_history
        )
        
        return {
            "answer": answer,
            "sources": [
                {
                    "content": result['content'][:200] + "...",
                    "metadata": result['metadata'],
                    "relevance": 1 - result.get('distance', 0)
                }
                for result in context_results
            ]
        }
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"回答问题时发生错误: {str(e)}")

@app.post("/deep-read")
async def deep_read_analysis(request: DeepReadRequest):
    """深度阅读分析"""
    if request.document_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        doc_info = documents_db[request.document_id]
        full_text = ' '.join([section for section in doc_info['sections'].values()])
        
        # 深度分析
        analysis = deepseek_client.deep_read_analysis(full_text)
        
        # 提取关键概念
        key_concepts = deepseek_client.extract_key_concepts(full_text)
        
        return {
            "document_id": request.document_id,
            "analysis": analysis,
            "key_concepts": key_concepts
        }
    except Exception as e:
        logger.error(f"Error in deep read analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"深度分析时发生错误: {str(e)}")

@app.post("/knowledge-expansion")
async def knowledge_expansion(request: KnowledgeExpansionRequest):
    """知识发散与关联"""
    if request.document_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        doc_info = documents_db[request.document_id]
        full_text = ' '.join([section for section in doc_info['sections'].values()])
        
        # 知识发散分析
        expansion = deepseek_client.knowledge_expansion(request.topic, full_text)
        
        return {
            "document_id": request.document_id,
            "topic": request.topic,
            "expansion": expansion
        }
    except Exception as e:
        logger.error(f"Error in knowledge expansion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"知识发散分析时发生错误: {str(e)}")

@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        vector_stats = vector_store.get_collection_stats()
        
        return {
            "total_documents": len(documents_db),
            "vector_db_stats": vector_stats,
            "system_status": "healthy"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息时发生错误: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
