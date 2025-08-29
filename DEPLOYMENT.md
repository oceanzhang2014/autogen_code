# AutoGen Multi-Agent System - Deployment Guide

## 📋 Overview

This document provides comprehensive instructions for deploying and running the AutoGen Multi-Agent Code Generation System in both development and production environments.

## 🔧 System Requirements

### Minimum Requirements
- **Python**: 3.10 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for model API access

### Supported Platforms
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, CentOS 7+, Debian 10+)

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Context-Engineering-Intro
```

### 2. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Flask secret key
SECRET_KEY=your-super-secret-key-here

# Model Provider API Keys (at least one required)
DEEPSEEK_API_KEY=your-deepseek-api-key
MOONSHOT_API_KEY=your-moonshot-api-key
ALIBABA_API_KEY=your-alibaba-api-key
OPENAI_API_KEY=your-openai-api-key

# Optional: Ollama local setup
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Application settings
HOST=0.0.0.0
PORT=5011
FLASK_DEBUG=false
LOG_LEVEL=INFO
```

### 2. Model Configuration

The system uses `config/models.yaml` for model configurations. Default configuration supports:

- **DeepSeek**: Cost-effective, high-performance models
- **Moonshot**: Chinese language optimization
- **Alibaba**: Qwen model family
- **OpenAI**: GPT-3.5/GPT-4 models
- **Ollama**: Local model hosting

Example configuration:
```yaml
models:
  deepseek:
    provider: "deepseek"
    config:
      model: "deepseek-chat"
      api_key: "${DEEPSEEK_API_KEY}"
      base_url: "https://api.deepseek.com"
```

### 3. Agent Configuration

Agents are configured in `config/agents.yaml`:

```yaml
agents:
  code_generator:
    system_prompt: "You are a senior software engineer..."
    temperature: 0.7
    max_tokens: 2000
  
  quality_checker:
    system_prompt: "You are a code quality expert..."
    temperature: 0.3
    max_tokens: 1500
```

## 🚀 Running the Application

### Development Mode

1. **Start the application:**
```bash
python run.py
```

2. **Access the web interface:**
   - Open browser: `http://localhost:5011`
   - Health check: `http://localhost:5011/health`
   - API docs: `http://localhost:5011/api/models`

### Production Mode

#### Using Gunicorn (Linux/macOS)

1. **Install Gunicorn:**
```bash
pip install gunicorn
```

2. **Start the server:**
```bash
gunicorn -w 4 -b 0.0.0.0:5011 --timeout 300 "web.app:create_app()"
```

#### Using Waitress (Windows)

1. **Install Waitress:**
```bash
pip install waitress
```

2. **Start the server:**
```bash
waitress-serve --host=0.0.0.0 --port=5000 --call web.app:create_app
```

#### Docker Deployment

1. **Create Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5011", "--timeout", "300", "web.app:create_app()"]
```

2. **Build and run:**
```bash
docker build -t autogen-system .
docker run -p 5000:5011 --env-file .env autogen-system
```

## 🔍 Verification & Testing

### Health Checks

1. **Application Health:**
```bash
curl http://localhost:5011/health
```
Expected response:
```json
{"status": "healthy", "service": "autogen-multi-agent-system"}
```

2. **Model Availability:**
```bash
curl http://localhost:5011/api/models
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_web.py -v
python -m pytest tests/test_integration.py -v
```

### Sample API Request

```bash
curl -X POST http://localhost:5011/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a function to calculate fibonacci numbers",
    "language": "python",
    "max_iterations": 3
  }'
```

## 📊 Monitoring & Logging

### Log Files

- **Application logs**: `autogen_system.log`
- **Error tracking**: Check console output
- **Access logs**: Configure through web server

### Log Levels

Set via environment variable:
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Performance Monitoring

Monitor these key metrics:
- Response times for code generation
- Model API latency
- Memory usage during agent collaboration
- Concurrent session handling

## 🛠️ Troubleshooting

### Common Issues

1. **"No model provider API keys found"**
   - Ensure at least one API key is configured in `.env`
   - Verify API key validity with provider

2. **"Missing configuration files"**
   - Check `config/models.yaml` exists
   - Check `config/agents.yaml` exists
   - Verify YAML syntax is valid

3. **"This event loop is already running"**
   - Restart the application
   - Check for conflicting async operations

4. **Port already in use**
   ```bash
   # Find process using port 5000
   netstat -ano | findstr :5011  # Windows
   lsof -i :5011                 # Linux/macOS
   
   # Kill process or change port
   PORT=5001 python run.py
   ```

### Debug Mode

Enable debug mode for development:
```bash
FLASK_DEBUG=true python run.py
```

### Model Fallback

If primary models fail, the system automatically falls back to available models:
1. DeepSeek → Moonshot → Alibaba → OpenAI → Ollama

## 🔒 Security Considerations

### Production Security

1. **Environment Variables:**
   - Never commit `.env` files
   - Use secure secret management in production
   - Rotate API keys regularly

2. **Network Security:**
   - Use HTTPS in production
   - Configure firewall rules
   - Implement rate limiting

3. **Input Validation:**
   - The system includes built-in code safety scanning
   - Input sanitization is automatically applied
   - XSS protection is enabled

### CORS Configuration

Default CORS allows:
- `http://localhost:3000` (React development)
- `http://localhost:5011` (Flask development)

Modify in `web/app.py` for production domains.

## 📈 Scaling

### Horizontal Scaling

1. **Load Balancer Setup:**
   - Use nginx or AWS ALB
   - Configure session affinity if needed
   - Health check endpoint: `/health`

2. **Database for Sessions:**
   - Consider Redis for session storage
   - Implement distributed session management

### Performance Optimization

1. **Model Caching:**
   - Implement response caching
   - Use model-specific optimizations

2. **Resource Management:**
   - Monitor memory usage
   - Implement connection pooling
   - Configure appropriate timeouts

## 🚀 Production Checklist

- [ ] Environment variables configured
- [ ] API keys validated
- [ ] Configuration files present
- [ ] Health checks passing
- [ ] Tests passing (43/43)
- [ ] Logging configured
- [ ] Security headers configured
- [ ] HTTPS enabled
- [ ] Monitoring setup
- [ ] Backup procedures defined

## 📞 Support

### Getting Help

1. **Check logs:** `autogen_system.log`
2. **Verify configuration:** Run health checks
3. **Test connectivity:** Verify API keys work
4. **Community:** Check project issues and documentation

### Performance Tuning

Adjust these parameters based on your needs:
- `max_iterations`: Control conversation length
- `temperature`: Adjust creativity vs consistency
- `max_tokens`: Control response length
- `timeout`: Adjust for network conditions

---

**Note**: This system requires active internet connection for model API access unless using Ollama with local models.