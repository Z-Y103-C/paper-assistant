# 论文阅读助手 - AI+RAG系统

一个基于DeepSeek API和RAG（检索增强生成）技术的智能论文阅读辅助系统。

## 功能特性

- 📄 **文档管理**：支持PDF和DOCX格式论文的上传和管理
- 🔍 **智能检索**：基于向量数据库的语义搜索
- 💬 **智能问答**：利用DeepSeek API进行论文相关问答
- 📝 **论文摘要**：自动生成论文摘要
- 📖 **精读模式**：深度分析论文的研究问题、方法论、实验结果等
- 🌐 **知识发散**：发现相关研究方向、技术和交叉学科

## 技术栈

### 后端
- **FastAPI**：高性能Web框架
- **LangChain**：LLM应用开发框架
- **ChromaDB**：向量数据库
- **SentenceTransformers**：文本向量化
- **DeepSeek API**：AI模型服务

### 前端
- **HTML5/CSS3**：现代界面设计
- **Bootstrap 5**：响应式UI框架
- **JavaScript**：交互逻辑

## 项目结构

```
paper_assistant/
├── backend/
│   ├── main.py                 # FastAPI主应用
│   ├── config.py               # 配置管理
│   ├── document_loader.py      # 文档加载器
│   ├── text_processor.py       # 文本处理器
│   ├── vector_store.py         # 向量数据库管理
│   ├── deepseek_client.py      # DeepSeek API客户端
│   ├── requirements.txt        # Python依赖
│   └── .env.example           # 环境变量示例
├── frontend/
│   ├── index.html              # 主页面
│   └── app.js                  # 前端逻辑
├── data/
│   ├── papers/                 # 上传的论文存储
│   └── vector_db/             # 向量数据库存储
└── README.md                   # 项目说明
```

## 安装步骤

### 1. 环境要求

- Python 3.8+
- pip
- 现代浏览器

### 2. 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，填入你的DeepSeek API密钥
# DEEPSEEK_API_KEY=your_actual_api_key_here
```

### 4. 启动后端服务

```bash
# 在backend目录下运行
python main.py
```

后端服务将在 `http://localhost:8000` 启动

### 5. 启动前端

直接在浏览器中打开 `frontend/index.html` 文件，或使用本地服务器：

```bash
# 使用Python的简单HTTP服务器
cd frontend
python -m http.server 8080
```

然后在浏览器中访问 `http://localhost:8080`

## 使用说明

### 1. 上传文档
- 点击"上传文档"区域或拖拽PDF/DOCX文件到上传区域
- 等待文档处理完成

### 2. 智能问答
- 在"智能问答"标签页中输入问题
- 系统会基于上传的论文内容回答你的问题
- 支持多轮对话

### 3. 关键词搜索
- 在"关键词搜索"标签页中输入关键词
- 系统会返回相关度最高的论文片段

### 4. 论文摘要
- 在"论文摘要"标签页中选择文档
- 点击"生成摘要"按钮
- 系统会自动生成论文摘要

### 5. 精读论文
- 在"精读论文"标签页中选择文档
- 点击"开始精读"按钮
- 系统会提供深度分析，包括：
  - 核心研究问题
  - 主要方法论和创新点
  - 实验设计和数据集
  - 关键结果和发现
  - 研究局限性和未来方向
  - 与相关工作的对比
  - 实际应用价值

### 6. 知识发散
- 在"知识发散"标签页中选择文档
- 输入研究主题或关键词
- 点击"开始知识发散"按钮
- 系统会提供：
  - 相关研究主题和方向
  - 关键技术和方法
  - 可能的延伸研究方向
  - 相关的学术领域和交叉学科
  - 潜在的研究问题和挑战

## API文档

启动后端服务后，访问 `http://localhost:8000/docs` 查看完整的API文档。

主要API端点：

- `POST /upload` - 上传文档
- `GET /documents` - 获取文档列表
- `GET /documents/{document_id}` - 获取文档详情
- `DELETE /documents/{document_id}` - 删除文档
- `POST /search` - 搜索文档
- `POST /summary` - 生成摘要
- `POST /question` - 智能问答
- `POST /deep-read` - 深度阅读分析
- `POST /knowledge-expansion` - 知识发散分析

## 配置说明

在 `backend/.env` 文件中可以配置以下参数：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-b39a56b7d5814bfdac7d095f88789e99
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 文件存储配置
UPLOAD_DIR=../data/papers
VECTOR_DB_DIR=../data/vector_db
MAX_UPLOAD_SIZE=50

# 文本处理配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## 注意事项

1. **API密钥**：确保在 `.env` 文件中正确配置DeepSeek API密钥
2. **文件大小**：默认最大上传文件大小为50MB，可在配置中调整
3. **首次运行**：首次运行时会下载sentence-transformers模型，需要一些时间
4. **浏览器兼容性**：建议使用Chrome、Firefox或Edge等现代浏览器

## 故障排除

### 问题：上传文档失败
- 检查文件格式是否为PDF或DOCX
- 检查文件大小是否超过限制
- 查看后端日志了解详细错误信息

### 问题：AI回答质量不佳
- 确保DeepSeek API密钥正确配置
- 检查网络连接是否正常
- 尝试重新上传文档

### 问题：向量数据库错误
- 检查 `data/vector_db` 目录权限
- 尝试删除该目录重新初始化

## 开发计划

- [ ] 支持更多文档格式（TXT、Markdown等）
- [ ] 添加用户认证和多用户支持
- [ ] 实现文档标签和分类功能
- [ ] 添加论文引用管理
- [ ] 支持批量文档上传
- [ ] 添加数据可视化功能
- [ ] 实现论文对比分析
- [ ] 添加导出功能（PDF、Word等）

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发者。

---

**祝你使用愉快！如果觉得这个项目有用，请给个Star支持一下！**
