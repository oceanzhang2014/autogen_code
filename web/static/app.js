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
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        // Form elements
        this.form = document.getElementById('generation-form');
        this.generateBtn = document.getElementById('generate-btn');
        
        // Display elements
        this.conversation = document.getElementById('conversation');
        this.outputPanel = document.getElementById('output-panel');
        this.finalCode = document.getElementById('final-code');
        
        // Action buttons
        this.copyCodeBtn = document.getElementById('copy-code-btn');
        this.approveBtn = document.getElementById('approve-btn');
        this.rejectBtn = document.getElementById('reject-btn');
        
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
        this.approveBtn.addEventListener('click', () => this.approveCode());
        this.rejectBtn.addEventListener('click', () => this.showFeedbackModal());
        
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
        this.hideOutputPanel();
        
        try {
            const response = await fetch('/api/generate', {
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
        
        this.eventSource = new EventSource(`/api/stream/${sessionId}`);
        
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
                this.showFinalCode(data.code, data.language);
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
    
    showFinalCode(code, language) {
        const codeElement = this.finalCode.querySelector('code');
        codeElement.textContent = code;
        codeElement.className = `language-${language}`;
        
        // Update language indicator if exists
        const languageIndicator = this.outputPanel.querySelector('.final-code-language');
        if (languageIndicator) {
            languageIndicator.textContent = language.toUpperCase();
        }
        
        // Apply syntax highlighting
        if (window.Prism) {
            Prism.highlightElement(codeElement);
        }
        
        this.outputPanel.style.display = 'block';
        this.scrollToElement(this.outputPanel);
    }
    
    async copyCode() {
        const code = this.finalCode.querySelector('code').textContent;
        
        try {
            // 优先使用现代 Clipboard API（仅在 HTTPS 或 localhost 下可用）
            if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
                await navigator.clipboard.writeText(code);
                this.showSuccess('代码已复制到剪贴板！');
            } else {
                // 降级到传统方法
                this.fallbackCopyTextToClipboard(code);
            }
        } catch (error) {
            console.error('复制失败:', error);
            // 尝试降级方法
            this.fallbackCopyTextToClipboard(code);
        }
    }
    
    async approveCode() {
        if (!this.currentSessionId) {
            this.showError('No active session');
            return;
        }
        
        try {
            const response = await fetch('/api/approve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    action: 'approve'
                })
            });
            
            if (!response.ok) {
                let errorMessage = '批准代码失败';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = `HTTP错误: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            this.showSuccess('代码批准成功！');
            this.resetMessageChain(); // Reset chain for approval messages
            this.addMessage('user_proxy', '用户批准了代码。', new Date().toISOString());
            
        } catch (error) {
            console.error('Approve error:', error);
            this.showError(`批准代码失败: ${error.message}`);
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
            const response = await fetch('/api/user_input', {
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
            const response = await fetch('/api/user_input', {
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
            const response = await fetch('/api/approve', {
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
            this.generateBtn.innerHTML = '<span class="loading"></span> Generating...';
        } else {
            this.generateBtn.innerHTML = '🚀 Generate Code';
        }
    }
    
    clearConversation() {
        this.conversation.innerHTML = '';
        this.lastMessageAgent = null;
        this.lastMessageElement = null;
    }
    
    hideOutputPanel() {
        this.outputPanel.style.display = 'none';
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
            const debugResponse = await fetch('/api/debug_sessions');
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
            const statusResponse = await fetch(`/api/status/${this.currentSessionId}`);
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