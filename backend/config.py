import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = "deepseek-chat"
    
    # 文件存储配置
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../data/papers")
    VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "../data/vector_db")
    def _parse_size(size_str):
        """解析带单位的文件大小（如 50MB）"""
        size_str = str(size_str).upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # 如果没有单位，假设是字节
            return int(size_str)

    MAX_UPLOAD_SIZE = _parse_size(os.getenv("MAX_UPLOAD_SIZE", "50MB"))
    
    # 文本处理配置
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # 向量数据库配置
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # API配置
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    
    @classmethod
    def validate(cls):
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is required")
        
        # 创建必要的目录
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        os.makedirs(cls.VECTOR_DB_DIR, exist_ok=True)
        
        return True

config = Config()
