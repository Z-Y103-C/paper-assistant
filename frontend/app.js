// API配置
const API_BASE_URL = 'http://localhost:8000';

// 全局状态
let currentDocuments = [];
let selectedDocumentId = null;
let conversationHistory = [];

// DOM元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const documentList = document.getElementById('documentList');
const documentCount = document.getElementById('documentCount');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    // 文件上传
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    // 智能问答
    document.getElementById('sendQuestion').addEventListener('click', sendQuestion);
    document.getElementById('questionInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuestion();
    });

    // 搜索
    document.getElementById('searchButton').addEventListener('click', searchDocuments);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchDocuments();
    });

    // 摘要
    document.getElementById('generateSummary').addEventListener('click', generateSummary);

    // 精读
    document.getElementById('startDeepRead').addEventListener('click', startDeepRead);

    // 知识发散
    document.getElementById('startExpansion').addEventListener('click', startExpansion);
}

// 文件处理函数
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    showToast('正在上传文档...', 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('上传失败');
        }

        const result = await response.json();
        showToast('文档上传成功！', 'success');
        loadDocuments();
    } catch (error) {
        showToast('上传失败: ' + error.message, 'error');
    }
}

// 加载文档列表
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);
        const data = await response.json();
        currentDocuments = data.documents;
        updateDocumentList();
        updateDocumentSelects();
    } catch (error) {
        console.error('加载文档列表失败:', error);
    }
}

// 更新文档列表显示
function updateDocumentList() {
    documentCount.textContent = currentDocuments.length;

    if (currentDocuments.length === 0) {
        documentList.innerHTML = '<p class="text-muted text-center small">暂无文档</p>';
        return;
    }

    documentList.innerHTML = currentDocuments.map(doc => `
        <div class="document-item ${selectedDocumentId === doc.document_id ? 'active' : ''}" 
             data-id="${doc.document_id}"
             onclick="selectDocument('${doc.document_id}')">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">${doc.filename}</h6>
                    <small class="text-muted">
                        <i class="bi bi-file-earmark me-1"></i>${doc.file_type.toUpperCase()}
                        <span class="mx-2">|</span>
                        <i class="bi bi-clock me-1"></i>${formatDate(doc.upload_time)}
                    </small>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); deleteDocument('${doc.document_id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// 更新文档选择下拉框
function updateDocumentSelects() {
    const selects = ['summaryDocumentSelect', 'deepreadDocumentSelect', 'expansionDocumentSelect'];
    const options = '<option value="">请选择文档</option>' + 
        currentDocuments.map(doc => `<option value="${doc.document_id}">${doc.filename}</option>`).join('');

    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = options;
        }
    });
}

// 选择文档
function selectDocument(documentId) {
    selectedDocumentId = documentId;
    updateDocumentList();
}

// 删除文档
async function deleteDocument(documentId) {
    if (!confirm('确定要删除这个文档吗？')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('删除失败');
        }

        showToast('文档删除成功', 'success');
        loadDocuments();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// 发送问题
async function sendQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();

    if (!question) return;

    // 添加用户消息到聊天界面
    addMessageToChat('user', question);
    questionInput.value = '';

    // 显示加载状态
    showLoading('chatLoading');

    try {
        const response = await fetch(`${API_BASE_URL}/question`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                document_id: selectedDocumentId,
                conversation_history: conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error('请求失败');
        }

        const result = await response.json();

        // 添加助手回复到聊天界面
        addMessageToChat('assistant', result.answer, result.sources);

        // 更新对话历史
        conversationHistory.push({ role: 'user', content: question });
        conversationHistory.push({ role: 'assistant', content: result.answer });

    } catch (error) {
        addMessageToChat('assistant', '抱歉，我遇到了一些问题，请稍后重试。');
    } finally {
        hideLoading('chatLoading');
    }
}

// 添加消息到聊天界面
function addMessageToChat(type, content, sources = null) {
    const chatContainer = document.getElementById('chatContainer');

    // 清除初始提示
    if (chatContainer.querySelector('.text-center')) {
        chatContainer.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <div class="message-content">${formatMessage(content)}</div>
        ${sources ? `<div class="mt-2"><small class="text-muted">参考来源</small></div>` : ''}
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 格式化消息内容
function formatMessage(content) {
    // 简单的格式化，可以进一步扩展
    return content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// 搜索文档
async function searchDocuments() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();

    if (!query) return;

    showLoading('searchResults', '正在搜索...');

    try {
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query, n_results: 5 })
        });

        if (!response.ok) {
            throw new Error('搜索失败');
        }

        const result = await response.json();
        displaySearchResults(result.results);
    } catch (error) {
        document.getElementById('searchResults').innerHTML = `
            <div class="alert alert-danger">搜索失败: ${error.message}</div>
        `;
    }
}

// 显示搜索结果
function displaySearchResults(results) {
    const container = document.getElementById('searchResults');

    if (results.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">没有找到相关内容</p>';
        return;
    }

    container.innerHTML = results.map((result, index) => `
        <div class="search-result">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="mb-0">结果 ${index + 1}</h6>
                <span class="badge bg-primary">相关度: ${(result.relevance * 100).toFixed(1)}%</span>
            </div>
            <p class="mb-2">${result.content.substring(0, 200)}...</p>
            ${result.metadata ? `
                <small class="text-muted">
                    章节: ${result.metadata.section || '未知'}
                    ${result.metadata.chunk_id !== undefined ? ` | 块: ${result.metadata.chunk_id}` : ''}
                </small>
            ` : ''}
        </div>
    `).join('');
}

// 生成摘要
async function generateSummary() {
    const documentId = document.getElementById('summaryDocumentSelect').value;

    if (!documentId) {
        showToast('请先选择文档', 'warning');
        return;
    }

    showLoading('summaryLoading');

    try {
        const response = await fetch(`${API_BASE_URL}/summary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ document_id: documentId })
        });

        if (!response.ok) {
            throw new Error('生成摘要失败');
        }

        const result = await response.json();
        document.getElementById('summaryResult').innerHTML = `
            <div class="alert alert-success">
                <h6><i class="bi bi-file-text me-2"></i>论文摘要</h6>
                <p>${result.summary}</p>
            </div>
        `;
    } catch (error) {
        document.getElementById('summaryResult').innerHTML = `
            <div class="alert alert-danger">生成摘要失败: ${error.message}</div>
        `;
    } finally {
        hideLoading('summaryLoading');
    }
}

// 开始精读
async function startDeepRead() {
    const documentId = document.getElementById('deepreadDocumentSelect').value;

    if (!documentId) {
        showToast('请先选择文档', 'warning');
        return;
    }

    showLoading('deepreadLoading');

    try {
        const response = await fetch(`${API_BASE_URL}/deep-read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ document_id: documentId })
        });

        if (!response.ok) {
            throw new Error('深度分析失败');
        }

        const result = await response.json();
        displayDeepReadResult(result);
    } catch (error) {
        document.getElementById('deepreadResult').innerHTML = `
            <div class="alert alert-danger">深度分析失败: ${error.message}</div>
        `;
    } finally {
        hideLoading('deepreadLoading');
    }
}

// 显示精读结果
function displayDeepReadResult(result) {
    const container = document.getElementById('deepreadResult');

    let analysisHTML = '';
    for (const [section, content] of Object.entries(result.analysis)) {
        analysisHTML += `
            <div class="analysis-section">
                <h6>${section}</h6>
                <p>${content}</p>
            </div>
        `;
    }

    const conceptsHTML = result.key_concepts.map(concept =>
        `<span class="concept-tag">${concept}</span>`
    ).join('');

    container.innerHTML = `
        <h5 class="mb-3"><i class="bi bi-book me-2"></i>深度阅读分析</h5>
        ${analysisHTML}
        <div class="mt-4">
            <h6>关键概念</h6>
            <div>${conceptsHTML}</div>
        </div>
    `;
}

// 开始知识发散
async function startExpansion() {
    const documentId = document.getElementById('expansionDocumentSelect').value;
    const topic = document.getElementById('expansionTopic').value.trim();

    if (!documentId || !topic) {
        showToast('请选择文档并输入研究主题', 'warning');
        return;
    }

    showLoading('expansionLoading');

    try {
        const response = await fetch(`${API_BASE_URL}/knowledge-expansion`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                document_id: documentId,
                topic: topic
            })
        });

        if (!response.ok) {
            throw new Error('知识发散分析失败');
        }

        const result = await response.result();
        displayExpansionResult(result);
    } catch (error) {
        document.getElementById('expansionResult').innerHTML = `
            <div class="alert alert-danger">知识发散分析失败: ${error.message}</div>
        `;
    } finally {
        hideLoading('expansionLoading');
    }
}

// 显示知识发散结果
function displayExpansionResult(result) {
    const container = document.getElementById('expansionResult');
    const expansion = result.expansion;

    const sections = [
        { key: 'related_topics', title: '相关研究主题' },
        { key: 'key_technologies', title: '关键技术' },
        { key: 'research_directions', title: '延伸研究方向' },
        { key: 'interdisciplinary_fields', title: '交叉学科领域' },
        { key: 'research_challenges', title: '研究挑战' }
    ];

    let html = `<h5 class="mb-3"><i class="bi bi-diagram-3 me-2"></i>知识发散分析</h5>`;

    sections.forEach(section => {
        if (expansion[section.key] && expansion[section.key].length > 0) {
            html += `
                <div class="expansion-card">
                    <h6>${section.title}</h6>
                    <ul>
                        ${expansion[section.key].map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    });

    container.innerHTML = html;
}

// 工具函数
function showLoading(elementId, message = '加载中...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        `;
    }
}

function hideLoading(elementId) {
    // 对于有专门loading元素的，隐藏它们
    const loadingElement = document.getElementById(elementId + 'Loading');
    if (loadingElement) {
        loadingElement.classList.remove('show');
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    // 设置颜色
    toast.className = `toast align-items-center text-white border-0 bg-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : type === 'success' ? 'success' : 'primary'}`;
    toastMessage.textContent = message;

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
