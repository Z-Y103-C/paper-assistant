from openai import OpenAI
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "deepseek-chat"
    
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """发送聊天请求"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """生成论文摘要"""
        system_prompt = """你是一个专业的学术助手，擅长总结学术论文。请根据提供的论文内容生成一个简洁、准确的摘要。
摘要应该包含：
1. 研究背景和问题
2. 主要方法和创新点
3. 关键结果和结论
4. 研究意义和贡献

摘要长度控制在{}字以内。""".format(max_length)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请为以下论文内容生成摘要：\n\n{text}"}
        ]
        
        return self.chat_completion(messages, temperature=0.5, max_tokens=800)
    
    def answer_question(self, question: str, context: str, conversation_history: List[Dict] = None) -> str:
        """基于上下文回答问题"""
        system_prompt = """你是一个专业的学术助手，专门帮助用户理解和分析论文。
请基于提供的论文内容回答用户的问题。如果问题无法从提供的上下文中找到答案，请诚实地说明。
回答要准确、清晰，并尽可能引用论文中的具体内容。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"论文内容：\n{context}\n\n问题：{question}"}
        ]
        
        # 如果有对话历史，添加到消息中
        if conversation_history:
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": f"论文内容：\n{context}\n\n问题：{question}"})
        
        return self.chat_completion(messages, temperature=0.3, max_tokens=1500)
    
    def deep_read_analysis(self, paper_content: str) -> Dict[str, str]:
        """深度阅读分析论文"""
        system_prompt = """你是一个专业的学术分析助手，擅长深度分析学术论文。
请对论文进行全面分析，包括方法论、实验设计、结果分析、创新点等方面。"""
        
        analysis_prompt = f"""请对以下论文进行深度阅读分析，提供以下信息：

1. 核心研究问题
2. 主要方法论和创新点
3. 实验设计和数据集
4. 关键结果和发现
5. 研究局限性和未来方向
6. 与相关工作的对比
7. 实际应用价值

论文内容：
{paper_content}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.4, max_tokens=2000)
        
        # 解析返回的分析内容
        analysis_sections = {}
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if any(keyword in line.lower() for keyword in ['核心研究问题', '主要方法论', '实验设计', '关键结果', '研究局限性', '相关工作', '实际应用']):
                if current_section and current_content:
                    analysis_sections[current_section] = '\n'.join(current_content)
                current_section = line
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        if current_section and current_content:
            analysis_sections[current_section] = '\n'.join(current_content)
        
        return analysis_sections
    
    def knowledge_expansion(self, topic: str, related_content: str) -> Dict[str, List[str]]:
        """知识发散与关联分析"""
        system_prompt = """你是一个专业的学术知识关联助手，擅长发现和关联相关的研究内容。
请基于提供的研究主题和相关内容，进行知识发散和关联分析。"""
        
        prompt = f"""研究主题：{topic}

相关内容：
{related_content}

请提供以下分析：
1. 相关研究主题和方向
2. 关键技术和方法
3. 可能的延伸研究方向
4. 相关的学术领域和交叉学科
5. 潜在的研究问题和挑战"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.6, max_tokens=1500)
        
        # 解析返回的关联分析
        expansion = {
            'related_topics': [],
            'key_technologies': [],
            'research_directions': [],
            'interdisciplinary_fields': [],
            'research_challenges': []
        }
        
        current_category = None
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if '相关研究主题' in line or 'related topics' in line.lower():
                current_category = 'related_topics'
            elif '关键技术' in line or 'key technologies' in line.lower():
                current_category = 'key_technologies'
            elif '延伸研究' in line or 'research directions' in line.lower():
                current_category = 'research_directions'
            elif '交叉学科' in line or 'interdisciplinary' in line.lower():
                current_category = 'interdisciplinary_fields'
            elif '研究挑战' in line or 'research challenges' in line.lower():
                current_category = 'research_challenges'
            elif line.startswith('-') or line.startswith('•') or line.startswith('1.') or line.startswith('2.'):
                if current_category and len(line) > 2:
                    expansion[current_category].append(line.lstrip('-•0123456789. ').strip())
        
        return expansion
    
    def extract_key_concepts(self, text: str) -> List[str]:
        """提取关键概念"""
        system_prompt = """你是一个专业的学术概念提取助手。
请从提供的文本中提取最重要的学术概念和术语。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请从以下文本中提取关键概念（最多10个）：\n\n{text}"}
        ]
        
        response = self.chat_completion(messages, temperature=0.3, max_tokens=300)
        
        # 提取概念列表
        concepts = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('1.') or line.startswith('2.')):
                concept = line.lstrip('-•0123456789. ').strip()
                if concept:
                    concepts.append(concept)
        
        return concepts
