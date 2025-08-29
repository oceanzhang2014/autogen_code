## FEATURE:

基于AutoGen框架构建的多智能体代码生成、质量检查和优化系统，包含：

- **多智能体协作**: 代码生成器、质量检查器、优化器三个专门智能体协同工作
- **Flask后端**: 提供RESTful API接口，支持实时消息传递和智能体状态管理
- **HTML前端**: 支持Markdown渲染，代码高亮显示，一键复制功能
- **多模型支持**: 配置化支持DeepSeek、阿里云百炼、月之暗面、Ollama等多种大模型
- **实时流式输出**: 智能体输出立即显示在前端，包含发言者身份和内容
- **人工确认流程**: 用户可审查最终代码并提出修改建议或直接采用

## EXAMPLES:

参考 `examples/` 文件夹中的AutoGen示例：

- `examples/app_team.py` - 多智能体团队协作的基础架构，展示RoundRobinGroupChat模式
- `examples/flask_server.py` - Flask Blueprint架构参考，用于构建web服务
- `examples/model_config.yaml` - 模型配置文件模板，支持多种LLM提供商
- `examples/README.md` - AutoGen AgentChat框架使用指南和最佳实践

关键设计模式：
- 使用RoundRobinGroupChat实现智能体轮流对话
- TextMentionTermination条件控制对话终止
- ModelClientStreamingChunkEvent处理实时流式输出
- 用户会话管理存储智能体状态

## DOCUMENTATION:

**AutoGen AgentChat Framework**:
- 官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html
- 智能体类型: AssistantAgent, UserProxyAgent
- 团队配置: RoundRobinGroupChat, 终止条件管理
- 模型客户端: ChatCompletionClient配置和流式处理

**前端技术栈**:
- HTML/CSS/JavaScript原生开发
- Markdown渲染库 (如marked.js)
- 代码高亮库 (如Prism.js或highlight.js)
- WebSocket或Server-Sent Events用于实时通信

**后端架构**:
- Flask框架 + Blueprint模块化设计
- SQLAlchemy/SQLModel用于数据持久化
- python-dotenv环境变量管理
- Pydantic数据验证
- 后端在conda已经建立好的pyautogen的虚拟环境中运行

## OTHER CONSIDERATIONS:

**智能体角色设计**:
1. **CodeGenerator**: 根据需求生成初始代码
2. **QualityChecker**: 分析代码质量、安全性、最佳实践
3. **CodeOptimizer**: 优化性能、重构、改进代码结构
4. **UserProxy**: 处理用户输入和确认流程

**技术要点**:
- 非流式最终输出，但智能体间对话实时显示
- 前端状态管理区分智能体对话和最终结果
- 模型配置热加载，支持运行时切换LLM
- 错误处理和重试机制确保系统稳定性
- 代码安全扫描防止恶意代码生成

**配置文件结构**:
```yaml
models:
  deepseek:
    provider: "deepseek"
    api_key: "your_api_key"
    model: "deepseek-chat"
  
  moonshot:
    provider: "moonshot" 
    api_key: "your_api_key"
    model: "moonshot-v1-8k"
    
  alibaba:
    provider: "alibaba_bailian"
    api_key: "your_api_key"
    model: "qwen-max"
    
  ollama:
    provider: "ollama"
    base_url: "http://localhost:11434"
    model: "llama2"

agents:
  code_generator:
    model: "deepseek"
    system_prompt: "你是一个专业的代码生成专家..."
    
  quality_checker:  
    model: "moonshot"
    system_prompt: "你是一个代码质量检查专家..."
    
  code_optimizer:
    model: "alibaba" 
    system_prompt: "你是一个代码优化专家..."
```

**开发优先级**:
1. 搭建基础Flask应用和AutoGen智能体框架
2. 实现基本的三智能体协作流程
3. 开发前端界面和实时通信功能
4. 集成多模型配置和切换功能
5. 完善用户交互和确认流程
6. 添加错误处理和日志记录
7. 性能优化和安全增强