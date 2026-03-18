import re
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """文本处理器，负责文本分块和预处理"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """清理文本，移除多余的空白和特殊字符"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除页码
        text = re.sub(r'\b\d+\s*(?:page|p\.)\b', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def split_by_sentences(self, text: str) -> List[str]:
        """按句子分割文本"""
        # 简单的句子分割逻辑
        sentences = re.split(r'(?<=[.!?。！？])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """将文本分割成块"""
        cleaned_text = self.clean_text(text)
        sentences = self.split_by_sentences(cleaned_text)
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            if current_size + sentence_size <= self.chunk_size:
                current_chunk += sentence + " "
                current_size += sentence_size + 1
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': {
                            **(metadata or {}),
                            'chunk_id': len(chunks),
                            'start_sentence': i - len(self.split_by_sentences(current_chunk)),
                            'end_sentence': i - 1
                        }
                    })
                
                # 创建重叠部分
                overlap_sentences = self.split_by_sentences(current_chunk)[-self.chunk_overlap//100:]
                current_chunk = " ".join(overlap_sentences) + " " + sentence + " "
                current_size = len(current_chunk)
        
        # 添加最后一个块
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': {
                    **(metadata or {}),
                    'chunk_id': len(chunks),
                    'start_sentence': len(sentences) - len(self.split_by_sentences(current_chunk)),
                    'end_sentence': len(sentences) - 1
                }
            })
        
        return chunks
    
    def chunk_sections(self, sections: Dict[str, str], document_id: str) -> List[Dict]:
        """按章节分块文本"""
        all_chunks = []
        
        for section_name, section_text in sections.items():
            if section_text.strip():
                chunks = self.chunk_text(section_text, {
                    'section': section_name,
                    'document_id': document_id
                })
                all_chunks.extend(chunks)
        
        return all_chunks
    
    def extract_key_terms(self, text: str, top_n: int = 20) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取逻辑
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        
        # 过滤常见词
        stop_words = {'the', 'and', 'that', 'have', 'for', 'not', 'with', 'this', 'but', 'from', 'they', 'which', 'their', 'would', 'been', 'there', 'could', 'about', 'after', 'before'}
        words = [w for w in words if w not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回高频词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取实体（简单版本）"""
        entities = {
            'methods': [],
            'datasets': [],
            'metrics': []
        }
        
        # 方法论相关词汇
        method_keywords = ['algorithm', 'method', 'approach', 'technique', 'model', 'framework', 'network', 'learning']
        for keyword in method_keywords:
            if keyword in text.lower():
                entities['methods'].append(keyword)
        
        # 数据集相关词汇
        dataset_keywords = ['dataset', 'data', 'corpus', 'benchmark', 'collection']
        for keyword in dataset_keywords:
            if keyword in text.lower():
                entities['datasets'].append(keyword)
        
        # 指标相关词汇
        metric_keywords = ['accuracy', 'precision', 'recall', 'f1', 'score', 'performance', 'evaluation']
        for keyword in metric_keywords:
            if keyword in text.lower():
                entities['metrics'].append(keyword)
        
        return entities
