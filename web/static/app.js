// Frontend JavaScript for AutoGen Multi-Agent Code Generator
class CodeGeneratorApp {
    constructor() {
        this.currentSessionId = null;
        this.eventSource = null;
        this.isGenerating = false;
        this.lastMessageAgent = null;
        this.lastMessageElement = null;
        
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
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            this.showError('Connection to server lost. Please try again.');
            this.setGenerating(false);
        };
        
        this.eventSource.onopen = () => {
            console.log('EventSource connection opened');
        };
    }
    
    handleStreamMessage(data) {
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
                // Keep connection alive
                break;
                
            default:
                console.log('Unknown message type:', data.type);
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
        // Basic markdown-like formatting
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    showFinalCode(code, language) {
        const codeElement = this.finalCode.querySelector('code');
        codeElement.textContent = code;
        codeElement.className = `language-${language}`;
        
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
            await navigator.clipboard.writeText(code);
            this.showSuccess('Code copied to clipboard!');
        } catch (error) {
            console.error('Failed to copy code:', error);
            this.showError('Failed to copy code to clipboard');
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
                const error = await response.json();
                throw new Error(error.error || 'Failed to approve code');
            }
            
            this.showSuccess('Code approved successfully!');
            this.resetMessageChain(); // Reset chain for approval messages
            this.addMessage('user_proxy', 'User approved the code.', new Date().toISOString());
            
        } catch (error) {
            this.showError(`Failed to approve code: ${error.message}`);
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
            this.showError('Please enter a message');
            return;
        }
        
        if (!this.currentSessionId) {
            this.showError('No active session');
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
                    content: message
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to send message');
            }
            
            this.hideUserInput();
            this.resetMessageChain(); // Reset chain for user messages
            this.addMessage('user_proxy', `User input: ${message}`, new Date().toISOString());
            this.showSuccess('Message sent successfully!');
            
        } catch (error) {
            this.showError(`Failed to send message: ${error.message}`);
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
                const error = await response.json();
                throw new Error(error.error || 'Failed to submit feedback');
            }
            
            this.hideFeedbackModal();
            this.showSuccess('Feedback submitted successfully!');
            this.resetMessageChain(); // Reset chain for feedback messages
            this.addMessage('user_proxy', `User requested changes: ${feedback}`, new Date().toISOString());
            
        } catch (error) {
            this.showError(`Failed to submit feedback: ${error.message}`);
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