// Frontend JavaScript for AutoGen Multi-Agent Code Generator
class CodeGeneratorApp {
    constructor() {
        this.currentSessionId = null;
        this.eventSource = null;
        this.isGenerating = false;
        this.lastMessageAgent = null;
        this.lastMessageElement = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;  // Back to reasonable number
        
        // Set global reference for code copying
        window.codeApp = this;
        
        // Determine API base path
        this.apiBase = this.getApiBasePath();
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    getApiBasePath() {
        // Determine the correct API path based on current URL
        const currentPath = window.location.pathname;
        if (currentPath.includes('/autogen/')) {
            return '/autogen/api';
        }
        return '/api';
    }
    
    initializeElements() {
        // Form elements
        this.form = document.getElementById('generation-form');
        this.generateBtn = document.getElementById('generate-btn');
        
        // Display elements
        this.conversation = document.getElementById('conversation');
        this.codeActions = document.getElementById('code-actions');
        
        // Action buttons
        this.copyCodeBtn = document.getElementById('copy-code-btn');
        
        // Modal elements
        this.feedbackModal = document.getElementById('feedback-modal');
        this.feedbackText = document.getElementById('feedback-text');
        this.submitFeedbackBtn = document.getElementById('submit-feedback-btn');
        this.cancelFeedbackBtn = document.getElementById('cancel-feedback-btn');
        
        // User input elements
        this.userInputArea = document.getElementById('user-input-area');
        this.inputPrompt = document.getElementById('input-prompt');
        this.userInputText = document.getElementById('user-input-text');
        this.sendUserMessageBtn = document.getElementById('send-user-message-btn');
        this.endTaskBtn = document.getElementById('end-task-btn');
    }
    
    attachEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Action buttons
        this.copyCodeBtn.addEventListener('click', () => this.copyCode());
        
        // Modal actions
        this.submitFeedbackBtn.addEventListener('click', () => this.submitFeedback());
        this.cancelFeedbackBtn.addEventListener('click', () => this.hideFeedbackModal());
        
        // Close modal on backdrop click
        this.feedbackModal.addEventListener('click', (e) => {
            if (e.target === this.feedbackModal) {
                this.hideFeedbackModal();
            }
        });
        
        // User input handling
        this.sendUserMessageBtn.addEventListener('click', () => this.sendUserMessage());
        this.endTaskBtn.addEventListener('click', () => this.endTask());
        this.userInputText.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendUserMessage();
            }
        });
    }
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        if (this.isGenerating) {
            return;
        }
        
        // Get form data
        const formData = new FormData(this.form);
        const requestData = {
            requirements: formData.get('requirements'),
            language: formData.get('language'),
            context: formData.get('context') || null,
            max_iterations: parseInt(formData.get('max_iterations'))
        };
        
        // Validate requirements
        if (!requestData.requirements.trim()) {
            this.showError('Please provide code requirements');
            return;
        }
        
        try {
            await this.startCodeGeneration(requestData);
        } catch (error) {
            this.showError(`Failed to start code generation: ${error.message}`);
        }
    }
    
    async startCodeGeneration(requestData) {
        this.setGenerating(true);
        this.clearConversation();
        this.hideCodeActions();
        
        try {
            const response = await fetch(`${this.apiBase}/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to start generation');
            }
            
            const data = await response.json();
            this.currentSessionId = data.session_id;
            
            // Start listening to the event stream
            this.startEventStream(data.session_id);
            
            this.addMessage('system', 'Code generation started...', new Date().toISOString());
            
        } catch (error) {
            this.setGenerating(false);
            throw error;
        }
    }
    
    startEventStream(sessionId) {
        // Close existing stream if any
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource(`${this.apiBase}/stream/${sessionId}`);
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleStreamMessage(data);
            } catch (error) {
                console.error('Error parsing stream message:', error);
                console.error('Raw event data:', event.data);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            console.log(`Connection readyState: ${this.eventSource.readyState}`);
            console.log(`EventSource.CONNECTING: ${EventSource.CONNECTING}`);
            console.log(`EventSource.OPEN: ${EventSource.OPEN}`);
            console.log(`EventSource.CLOSED: ${EventSource.CLOSED}`);
            
            // 检查连接状态
            if (this.eventSource.readyState === EventSource.CLOSED) {
                console.log('EventSource connection closed - will attempt reconnection');
                // 如果是在等待用户输入时，尝试静默重连
                const userInputVisible = this.userInputArea.style.display === 'block';
                console.log(`User input visible: ${userInputVisible}, isGenerating: ${this.isGenerating}`);
                
                if (this.isGenerating) {
                    if (userInputVisible) {
                        // 在用户输入期间，尝试静默重连
                        console.log('Attempting silent reconnection during user input wait');
                        this.attemptReconnection(sessionId);
                    } else {
                        // 非用户输入期间，显示错误
                        this.showError('与服务器的连接已断开，请重新尝试');
                        this.setGenerating(false);
                    }
                }
            } else if (this.eventSource.readyState === EventSource.CONNECTING) {
                console.log('EventSource reconnecting...');
                // 连接重试中，不显示错误
            } else {
                console.log('EventSource error occurred - checking if need to show error');
                // 如果正在生成中且不是在等待用户输入时才显示错误
                const userInputVisible = this.userInputArea.style.display === 'block';
                if (this.isGenerating && !userInputVisible) {
                    this.showError('连接出现问题，请检查网络');
                }
            }
        };
        
        this.eventSource.onopen = () => {
            console.log('EventSource connection opened');
            this.reconnectAttempts = 0; // Reset reconnection attempts on successful connection
        };
    }
    
    attemptReconnection(sessionId) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = 3000; // Fixed 3 second delay
            
            console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
            
            setTimeout(() => {
                if (this.currentSessionId === sessionId && this.isGenerating) {
                    console.log('Reconnecting EventSource...');
                    // Close existing connection first
                    if (this.eventSource) {
                        this.eventSource.close();
                    }
                    // Start new connection
                    this.startEventStream(sessionId);
                } else {
                    console.log('Session changed or generation stopped, cancelling reconnection');
                }
            }, delay);
        } else {
            console.log('Max reconnection attempts reached');
            this.showError('连接多次中断，请刷新页面重试');
        }
    }
    
    handleStreamMessage(data) {
        // Ensure data has a type field
        if (!data || typeof data !== 'object' || !data.type) {
            console.log('Invalid message format - missing type field:', data);
            return;
        }
        
        switch (data.type) {
            case 'agent_message':
                const isChunk = data.is_chunk || false;
                this.addMessage(data.agent, data.message, data.timestamp, isChunk);
                break;
                
            case 'code_output':
                this.resetMessageChain(); // Reset chain for code output
                this.showFinalCode(data.code, data.language, data.iteration, data.final_score);
                // Also show complete code in dialog for easy viewing
                this.showCompleteCodeDialog(data.code, data.language, data.iteration, data.final_score);
                break;
                
            case 'quality_score':
                this.resetMessageChain(); // Reset chain for quality scores
                this.showQualityScore(data.score, data.iteration);
                break;
                
            case 'system':
                this.resetMessageChain(); // Reset chain for system messages
                this.addMessage('system', data.message, data.timestamp);
                break;
                
            case 'error':
                this.resetMessageChain(); // Reset chain for errors
                this.showError(data.message);
                this.setGenerating(false);
                break;
                
            case 'stream_end':
                this.resetMessageChain(); // Reset chain at end
                this.setGenerating(false);
                this.eventSource.close();
                break;
                
            case 'input_request':
                this.resetMessageChain(); // Reset chain for user input requests
                this.showUserInput(data.prompt);
                break;
                
            case 'heartbeat':
                // Keep connection alive - just log periodically
                if (!this.lastHeartbeatLog || Date.now() - this.lastHeartbeatLog > 30000) {
                    console.log('Received heartbeat, connection alive');
                    this.lastHeartbeatLog = Date.now();
                }
                break;
                
            default:
                console.log('Unknown message type:', data.type, data);
        }
    }
    
    resetMessageChain() {
        this.lastMessageAgent = null;
        this.lastMessageElement = null;
    }
    
    addMessage(agent, content, timestamp, isChunk = false) {
        const time = new Date(timestamp).toLocaleTimeString();
        const agentName = this.getAgentDisplayName(agent);
        
        // Check if this is a continuation of the same agent's message
        if (this.lastMessageAgent === agent && this.lastMessageElement && isChunk) {
            // Append to existing message (for streaming chunks)
            const messageContent = this.lastMessageElement.querySelector('.message-content');
            
            // Get current raw content without HTML formatting
            if (!this.lastMessageElement.rawContent) {
                this.lastMessageElement.rawContent = '';
            }
            
            // Append new content to raw content
            this.lastMessageElement.rawContent += content;
            
            // Update the displayed content with formatting
            messageContent.innerHTML = this.formatMessage(this.lastMessageElement.rawContent);
            
            // Apply syntax highlighting to new code blocks
            this.highlightCodeBlocks(this.lastMessageElement);
            
            // Update timestamp
            const timeElement = this.lastMessageElement.querySelector('.message-time');
            timeElement.textContent = time;
        } else {
            // Create new message
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${agent}`;
            messageDiv.rawContent = content; // Store raw content
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span>${agentName}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-content">${this.formatMessage(content)}</div>
            `;
            
            this.conversation.appendChild(messageDiv);
            this.lastMessageAgent = agent;
            this.lastMessageElement = messageDiv;
            
            // Apply syntax highlighting to new code blocks
            this.highlightCodeBlocks(messageDiv);
        }
        
        this.scrollToBottom();
    }
    
    getAgentDisplayName(agent) {
        const names = {
            'system': '🔧 System',
            'code_generator': '👨‍💻 Code Generator',
            'quality_checker': '🔍 Quality Checker',
            'code_optimizer': '⚡ Code Optimizer',
            'user_proxy': '👤 User Proxy'
        };
        return names[agent] || agent;
    }
    
    formatMessage(content) {
        // Store placeholders for code blocks to protect them from line break conversion
        const codeBlockPlaceholders = [];
        let placeholderIndex = 0;
        
        // Handle code blocks first (triple backticks) - preserve original formatting
        content = content.replace(/```(\w+)?\s*\n([\s\S]*?)\n\s*```/g, (match, language, code) => {
            const lang = language || 'plaintext';
            const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
            
            // Preserve original code formatting - only trim the very first and last newlines
            const preservedCode = code.replace(/^\n/, '').replace(/\n$/, '');
            
            // Create code block with preserved formatting
            const codeBlock = `<div class="code-block">
                <div class="code-header">
                    <span class="code-language">${lang}</span>
                    <button class="copy-code-btn" onclick="window.codeApp.copyCodeBlock('${codeId}')">📋 复制代码</button>
                </div>
                <pre id="${codeId}"><code class="language-${lang}">${this.escapeHtml(preservedCode)}</code></pre>
            </div>`;
            
            // Store code block and return placeholder
            const placeholder = `__CODE_BLOCK_${placeholderIndex}__`;
            codeBlockPlaceholders[placeholderIndex] = codeBlock;
            placeholderIndex++;
            return placeholder;
        });
        
        // Also handle code blocks without language specification
        content = content.replace(/```\s*\n([\s\S]*?)\n\s*```/g, (match, code) => {
            const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
            const preservedCode = code.replace(/^\n/, '').replace(/\n$/, '');
            
            const codeBlock = `<div class="code-block">
                <div class="code-header">
                    <span class="code-language">CODE</span>
                    <button class="copy-code-btn" onclick="window.codeApp.copyCodeBlock('${codeId}')">📋 复制代码</button>
                </div>
                <pre id="${codeId}"><code class="language-plaintext">${this.escapeHtml(preservedCode)}</code></pre>
            </div>`;
            
            // Store code block and return placeholder
            const placeholder = `__CODE_BLOCK_${placeholderIndex}__`;
            codeBlockPlaceholders[placeholderIndex] = codeBlock;
            placeholderIndex++;
            return placeholder;
        });
        
        // Handle inline code (single backticks)
        content = content.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');
        
        // Basic markdown-like formatting
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert line breaks ONLY in non-code content
        content = content.replace(/\n/g, '<br>');
        
        // Restore code blocks from placeholders
        codeBlockPlaceholders.forEach((codeBlock, index) => {
            content = content.replace(`__CODE_BLOCK_${index}__`, codeBlock);
        });
        
        return content;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async copyCodeBlock(codeId) {
        const codeElement = document.getElementById(codeId);
        if (!codeElement) {
            this.showError('未找到代码块');
            return;
        }
        
        const code = codeElement.querySelector('code').textContent;
        
        try {
            // 优先使用现代 Clipboard API（仅在 HTTPS 或 localhost 下可用）
            if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
                await navigator.clipboard.writeText(code);
                this.showSuccess('代码已复制到剪贴板！');
            } else {
                // 降级到传统方法
                this.fallbackCopyTextToClipboard(code);
            }
        } catch (err) {
            console.error('复制失败:', err);
            // 尝试降级方法
            this.fallbackCopyTextToClipboard(code);
        }
    }
    
    fallbackCopyTextToClipboard(text) {
        try {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (successful) {
                this.showSuccess('代码已复制到剪贴板！');
            } else {
                this.showError('复制失败，请手动复制');
            }
        } catch (err) {
            console.error('降级复制方法也失败:', err);
            this.showError('复制失败，请手动复制');
        }
    }
    
    highlightCodeBlocks(element) {
        // Apply syntax highlighting using Prism.js if available
        if (window.Prism) {
            const codeBlocks = element.querySelectorAll('.code-block code');
            codeBlocks.forEach(codeBlock => {
                Prism.highlightElement(codeBlock);
            });
        }
    }
    
    showFinalCode(code, language, iteration = null, finalScore = null) {
        // Store the latest code for copying
        this.latestCode = code;
        this.latestLanguage = language;
        
        // Create a final code message in the conversation
        let messageText = `🎯 **最终代码生成完成**\n\n`;
        if (iteration !== null) {
            messageText += `**迭代轮次:** ${iteration}\n`;
        }
        if (finalScore !== null) {
            messageText += `**质量评分:** ${finalScore}/100\n`;
        }
        messageText += `**编程语言:** ${language.toUpperCase()}\n\n`;
        messageText += `\`\`\`${language}\n${code}\n\`\`\``;
        
        this.resetMessageChain();
        this.addMessage('system', messageText, new Date().toISOString());
        
        // Show the code actions in user input area
        this.showCodeActions();
    }
    
    showQualityScore(score, iteration) {
        // Create or update quality score display
        let scoreElement = document.querySelector('.quality-score-display');
        
        if (!scoreElement) {
            scoreElement = document.createElement('div');
            scoreElement.className = 'quality-score-display alert alert-info';
            scoreElement.style.cssText = `
                margin: 10px 0;
                padding: 10px 15px;
                border-radius: 5px;
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;
            
            // Insert before the chat messages container
            const chatContainer = document.querySelector('.chat-messages');
            if (chatContainer && chatContainer.parentNode) {
                chatContainer.parentNode.insertBefore(scoreElement, chatContainer);
            }
        }
        
        // Update score content
        const scoreText = `第${iteration}轮迭代 - 质量评分: ${score}/100`;
        const scoreColor = score >= 95 ? '#155724' : score >= 80 ? '#856404' : '#721c24';
        const backgroundColor = score >= 95 ? '#d4edda' : score >= 80 ? '#fff3cd' : '#f8d7da';
        
        scoreElement.innerHTML = `
            <span>${scoreText}</span>
            <span style="font-size: 1.2em;">${score >= 95 ? '✅' : score >= 80 ? '⚠️' : '❌'}</span>
        `;
        
        scoreElement.style.color = scoreColor;
        scoreElement.style.backgroundColor = backgroundColor;
        
        // Scroll to show the score
        this.scrollToElement(scoreElement);
    }
    
    showCompleteCodeDialog(code, language, iteration = null, finalScore = null) {
        // Create modal dialog for complete code display
        const existingModal = document.getElementById('complete-code-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        const modal = document.createElement('div');
        modal.id = 'complete-code-modal';
        modal.className = 'modal fade show complete-code-modal';
        modal.style.cssText = `
            display: block;
            background-color: rgba(0, 0, 0, 0.7);
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1050;
            animation: modalFadeIn 0.3s ease-out;
        `;
        
        const modalDialog = document.createElement('div');
        modalDialog.className = 'modal-dialog modal-xl complete-code-dialog';
        modalDialog.style.cssText = `
            max-width: 95%;
            width: 95%;
            height: 95%;
            margin: 2.5% auto;
            display: flex;
            flex-direction: column;
        `;
        
        // Build enhanced title with badges
        let titleText = `${language.toUpperCase()} 代码`;
        let badges = '';
        
        if (iteration !== null) {
            badges += `<span class="iteration-badge">第${iteration}轮</span>`;
        }
        if (finalScore !== null) {
            const scoreColor = finalScore >= 95 ? 'success' : finalScore >= 80 ? 'warning' : 'danger';
            badges += `<span class="score-badge badge-${scoreColor}">质量评分: ${finalScore}/100</span>`;
        }
        
        const codeLines = code.split('\n').length;
        const codeSize = new Blob([code]).size;
        const codeSizeKB = (codeSize / 1024).toFixed(1);
        
        modalDialog.innerHTML = `
            <div class="modal-content complete-code-content">
                <div class="modal-header complete-code-header">
                    <div class="modal-title-section">
                        <h4 class="modal-title">
                            <span class="code-icon">📄</span>
                            ${titleText}
                        </h4>
                        <div class="title-badges">
                            ${badges}
                        </div>
                    </div>
                    <button type="button" class="btn-close modern-close" onclick="this.closest('.modal').remove()" title="关闭 (ESC)">
                        <span class="close-icon">✕</span>
                    </button>
                </div>
                
                <div class="modal-body complete-code-body">
                    <div class="code-stats-bar">
                        <div class="code-stats">
                            <span class="stat-item">
                                <span class="stat-icon">📏</span>
                                <span class="stat-label">行数:</span>
                                <span class="stat-value">${codeLines}</span>
                            </span>
                            <span class="stat-item">
                                <span class="stat-icon">💾</span>
                                <span class="stat-label">大小:</span>
                                <span class="stat-value">${codeSizeKB} KB</span>
                            </span>
                            <span class="stat-item">
                                <span class="stat-icon">🔤</span>
                                <span class="stat-label">语言:</span>
                                <span class="stat-value">${language.toUpperCase()}</span>
                            </span>
                        </div>
                        <div class="code-actions-bar">
                            <button class="action-btn copy-btn" onclick="window.codeApp.copyCompleteCode()" title="复制到剪贴板 (Ctrl+C)">
                                <span class="btn-icon">📋</span>
                                <span class="btn-text">复制代码</span>
                            </button>
                            <button class="action-btn download-btn" onclick="window.codeApp.downloadCode()" title="下载代码文件">
                                <span class="btn-icon">⬇️</span>
                                <span class="btn-text">下载</span>
                            </button>
                        </div>
                    </div>
                    
                    <div class="code-display-container">
                        <div class="code-header">
                            <div class="code-header-left">
                                <span class="file-icon">📝</span>
                                <span class="file-name">generated_code.${this.getFileExtension(language)}</span>
                            </div>
                            <div class="code-header-right">
                                <button class="toggle-wrap-btn" onclick="window.codeApp.toggleLineWrap()" title="切换自动换行">
                                    <span class="wrap-icon">↩️</span>
                                </button>
                            </div>
                        </div>
                        <pre class="code-display" id="complete-code-pre"><code class="language-${language}" id="complete-code-content">${this.escapeHtml(code)}</code></pre>
                    </div>
                </div>
                
                <div class="modal-footer complete-code-footer">
                    <div class="footer-left">
                        <small class="generation-info">
                            <span class="info-icon">⏰</span>
                            生成时间: ${new Date().toLocaleString()}
                        </small>
                    </div>
                    <div class="footer-right">
                        <button type="button" class="btn btn-secondary close-btn" onclick="this.closest('.modal').remove()">
                            <span class="btn-icon">❌</span>
                            关闭
                        </button>
                        <button type="button" class="btn btn-primary copy-btn-main" onclick="window.codeApp.copyCompleteCode()">
                            <span class="btn-icon">📋</span>
                            复制代码
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        modal.appendChild(modalDialog);
        document.body.appendChild(modal);
        
        // Add keyboard event handlers
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modal.remove();
            } else if (e.ctrlKey && e.key === 'c') {
                e.preventDefault();
                this.copyCompleteCode();
            }
        });
        
        // Add click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Apply syntax highlighting
        if (window.Prism) {
            const codeElement = modal.querySelector('#complete-code-content');
            Prism.highlightElement(codeElement);
        }
        
        // Store code for copying and downloading
        this.completeCode = code;
        this.completeCodeLanguage = language;
        
        // Focus the modal for keyboard navigation
        modal.focus();
    }
    
    async copyCompleteCode() {
        if (!this.completeCode) {
            this.showError('没有找到要复制的代码');
            return;
        }
        
        try {
            if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
                await navigator.clipboard.writeText(this.completeCode);
                this.showSuccess('完整代码已复制到剪贴板！');
                
                // Update button text temporarily
                const copyButtons = document.querySelectorAll('.copy-btn, .copy-btn-main');
                copyButtons.forEach(btn => {
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<span class="btn-icon">✅</span><span class="btn-text">已复制</span>';
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                    }, 2000);
                });
            } else {
                this.fallbackCopyTextToClipboard(this.completeCode);
            }
        } catch (error) {
            console.error('复制失败:', error);
            this.fallbackCopyTextToClipboard(this.completeCode);
        }
    }
    
    downloadCode() {
        if (!this.completeCode) {
            this.showError('没有找到要下载的代码');
            return;
        }
        
        try {
            const language = this.completeCodeLanguage || 'txt';
            const extension = this.getFileExtension(language);
            const filename = `generated_code.${extension}`;
            
            const blob = new Blob([this.completeCode], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showSuccess(`代码已下载为 ${filename}`);
        } catch (error) {
            console.error('下载失败:', error);
            this.showError('下载失败，请重试');
        }
    }
    
    getFileExtension(language) {
        const extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'go': 'go',
            'rust': 'rs',
            'cpp': 'cpp',
            'c++': 'cpp',
            'csharp': 'cs',
            'c#': 'cs',
            'php': 'php',
            'ruby': 'rb',
            'swift': 'swift',
            'kotlin': 'kt',
            'scala': 'scala',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'shell': 'sh',
            'bash': 'sh',
            'yaml': 'yml',
            'json': 'json',
            'xml': 'xml',
            'markdown': 'md'
        };
        return extensions[language.toLowerCase()] || 'txt';
    }
    
    toggleLineWrap() {
        const codeDisplay = document.getElementById('complete-code-pre');
        const toggleBtn = document.querySelector('.toggle-wrap-btn');
        
        if (!codeDisplay || !toggleBtn) return;
        
        const isWrapped = codeDisplay.style.whiteSpace === 'pre-wrap';
        
        if (isWrapped) {
            // Switch to no wrap
            codeDisplay.style.whiteSpace = 'pre';
            codeDisplay.style.overflowX = 'auto';
            toggleBtn.innerHTML = '<span class="wrap-icon">↩️</span>';
            toggleBtn.title = '启用自动换行';
        } else {
            // Switch to wrap
            codeDisplay.style.whiteSpace = 'pre-wrap';
            codeDisplay.style.overflowX = 'hidden';
            toggleBtn.innerHTML = '<span class="wrap-icon">📄</span>';
            toggleBtn.title = '禁用自动换行';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async copyCode() {
        if (!this.latestCode) {
            this.showError('没有找到要复制的代码');
            return;
        }
        
        try {
            // 优先使用现代 Clipboard API（仅在 HTTPS 或 localhost 下可用）
            if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
                await navigator.clipboard.writeText(this.latestCode);
                this.showSuccess('代码已复制到剪贴板！');
            } else {
                // 降级到传统方法
                this.fallbackCopyTextToClipboard(this.latestCode);
            }
        } catch (error) {
            console.error('复制失败:', error);
            // 尝试降级方法
            this.fallbackCopyTextToClipboard(this.latestCode);
        }
    }
    
    
    showUserInput(prompt) {
        this.inputPrompt.textContent = prompt;
        this.userInputArea.style.display = 'block';
        this.userInputText.value = '';
        this.userInputText.focus();
    }
    
    hideUserInput() {
        this.userInputArea.style.display = 'none';
    }
    
    async sendUserMessage() {
        const message = this.userInputText.value.trim();
        
        if (!message) {
            this.showError('请输入消息内容');
            return;
        }
        
        if (!this.currentSessionId) {
            this.showError('当前没有活动会话');
            return;
        }
        
        console.log(`Sending user message to session: ${this.currentSessionId}`);
        console.log(`Message content: ${message}`);
        
        try {
            const response = await fetch(`${this.apiBase}/user_input`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    content: message
                })
            });
            
            if (!response.ok) {
                let errorMessage = '发送消息失败';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                    
                    // If session not found, try to check session status
                    if (response.status === 404 && errorMessage.includes('Session not found')) {
                        console.log('Session not found, checking session status...');
                        await this.checkSessionStatus();
                        return; // Don't throw error, let user try again
                    }
                } catch (e) {
                    errorMessage = `HTTP错误: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            this.hideUserInput();
            this.resetMessageChain(); // Reset chain for user messages
            this.addMessage('user_proxy', `用户反馈: ${message}`, new Date().toISOString());
            this.showSuccess('消息发送成功！');
            
        } catch (error) {
            console.error('User input error:', error);
            this.showError(`发送消息失败: ${error.message}`);
        }
    }
    
    async endTask() {
        if (!this.currentSessionId) {
            this.showError('当前没有活动会话');
            return;
        }
        
        // 确认对话框
        const confirmed = confirm('确定要结束当前任务吗？\n这将终止agent协作并完成代码生成流程。');
        if (!confirmed) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/user_input`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    content: 'TERMINATE'  // 发送终止信号
                })
            });
            
            if (!response.ok) {
                let errorMessage = '结束任务失败';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                    
                    // If session not found, try to check session status
                    if (response.status === 404 && errorMessage.includes('Session not found')) {
                        console.log('Session not found during end task, checking session status...');
                        await this.checkSessionStatus();
                        return; // Don't throw error, let user try again
                    }
                } catch (e) {
                    errorMessage = `HTTP错误: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            this.hideUserInput();
            this.resetMessageChain();
            this.addMessage('user_proxy', '用户选择结束任务', new Date().toISOString());
            this.showSuccess('任务已结束！');
            
        } catch (error) {
            console.error('End task error:', error);
            this.showError(`结束任务失败: ${error.message}`);
        }
    }

    showFeedbackModal() {
        this.feedbackText.value = '';
        this.feedbackModal.style.display = 'flex';
        this.feedbackText.focus();
    }
    
    hideFeedbackModal() {
        this.feedbackModal.style.display = 'none';
    }
    
    async submitFeedback() {
        const feedback = this.feedbackText.value.trim();
        
        if (!feedback) {
            this.showError('Please provide feedback');
            return;
        }
        
        if (!this.currentSessionId) {
            this.showError('No active session');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    action: 'reject',
                    feedback: feedback
                })
            });
            
            if (!response.ok) {
                let errorMessage = '提交反馈失败';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = `HTTP错误: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            this.hideFeedbackModal();
            this.showSuccess('反馈提交成功！');
            this.resetMessageChain(); // Reset chain for feedback messages
            this.addMessage('user_proxy', `用户请求修改: ${feedback}`, new Date().toISOString());
            
        } catch (error) {
            console.error('Submit feedback error:', error);
            this.showError(`提交反馈失败: ${error.message}`);
        }
    }
    
    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.generateBtn.disabled = isGenerating;
        
        if (isGenerating) {
            this.generateBtn.innerHTML = '<span class="loading"></span> 生成中...';
        } else {
            this.generateBtn.innerHTML = '🚀 生成代码';
        }
    }
    
    clearConversation() {
        this.conversation.innerHTML = '';
        this.lastMessageAgent = null;
        this.lastMessageElement = null;
    }
    
    showCodeActions() {
        if (this.codeActions) {
            this.codeActions.style.display = 'flex';
        }
    }
    
    hideCodeActions() {
        if (this.codeActions) {
            this.codeActions.style.display = 'none';
        }
    }
    
    scrollToBottom() {
        this.conversation.scrollTop = this.conversation.scrollHeight;
    }
    
    scrollToElement(element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    async checkSessionStatus() {
        if (!this.currentSessionId) {
            this.showError('没有当前会话ID');
            return;
        }
        
        try {
            console.log(`Checking status for session: ${this.currentSessionId}`);
            
            // First, check debug endpoint to see all sessions
            const debugResponse = await fetch(`${this.apiBase}/debug_sessions`);
            if (debugResponse.ok) {
                const debugData = await debugResponse.json();
                console.log('All sessions:', debugData);
                
                if (debugData.sessions && debugData.sessions[this.currentSessionId]) {
                    console.log('Session exists in debug data:', debugData.sessions[this.currentSessionId]);
                    this.showSuccess('会话已恢复，请重试发送消息');
                    return;
                }
            }
            
            // Try status endpoint
            const statusResponse = await fetch(`${this.apiBase}/status/${this.currentSessionId}`);
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                console.log('Session status:', statusData);
                this.showSuccess('会话状态正常，请重试发送消息');
            } else {
                console.log('Session status check failed, session may be lost');
                this.showError('会话已丢失，请重新开始代码生成');
                this.setGenerating(false);
                this.currentSessionId = null;
            }
        } catch (error) {
            console.error('Error checking session status:', error);
            this.showError('无法检查会话状态，请重新开始');
        }
    }


    showNotification(message, type) {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '8px',
            color: 'white',
            backgroundColor: type === 'error' ? '#dc2626' : '#059669',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            zIndex: '1001',
            animation: 'slideIn 0.3s ease-out'
        });
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CodeGeneratorApp();
});