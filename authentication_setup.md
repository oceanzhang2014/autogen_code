# AutoGen 系统认证功能

## 功能概述

已成功为AutoGen多智能体系统添加了完整的身份验证功能。系统现在要求用户登录后才能访问应用。

## 登录凭据

- **用户名**: `admin`
- **密码**: `qw123456`

## 新增文件

### 1. 认证工具模块
- `utils/auth.py` - 认证相关工具函数
  - 密码哈希验证
  - 会话管理
  - 登录状态检查
  - 路由保护装饰器

### 2. 登录页面
- `web/static/login.html` - 现代化登录界面
  - 响应式设计
  - 渐变背景
  - 实时表单验证
  - 错误和成功消息显示

### 3. 配置文件
- `authentication_setup.md` - 认证功能文档

## 修改的文件

### 1. Flask应用 (`web/app.py`)
- 添加会话超时配置
- 更新安全密钥
- 添加登录页面路由
- 主页面添加认证检查
- 添加登出路由

### 2. API路由 (`web/routes.py`)
- 添加登录API (`/api/login`)
- 添加登出API (`/api/logout`)
- 添加认证状态检查API (`/api/auth/status`)
- 为所有敏感路由添加`@login_required`装饰器

### 3. 前端界面
- **HTML** (`web/static/index.html`):
  - 添加用户信息显示
  - 添加登出按钮
  - 更新头部布局

- **JavaScript** (`web/static/app.js`):
  - 添加认证状态检查
  - 添加登出功能
  - 自动重定向到登录页面

- **CSS** (`web/static/style.css`):
  - 添加头部认证区域样式
  - 用户信息和登出按钮样式
  - 响应式设计支持

## 安全特性

### 1. 密码安全
- 使用SHA256哈希存储密码
- 不在代码中明文保存密码

### 2. 会话管理
- Flask会话机制
- 1小时会话超时
- 安全的会话密钥

### 3. 路由保护
- 所有敏感API都需要认证
- 主页面需要登录后访问
- API请求返回401状态码
- Web请求自动重定向到登录页

### 4. 前端安全
- 实时认证状态检查
- 自动处理未认证状态
- 安全的登出机制

## 用户体验

### 1. 登录流程
1. 访问主页自动跳转到登录页面
2. 输入用户名和密码
3. 实时验证和错误提示
4. 登录成功后跳转到主页

### 2. 已登录状态
- 头部显示用户信息
- 右上角显示登出按钮
- 所有功能正常使用

### 3. 登出流程
- 点击登出按钮
- 清除会话信息
- 自动跳转到登录页面

## 部署说明

### 1. 环境变量
可以在`.env`文件中设置自定义会话密钥：
```bash
SECRET_KEY=your-custom-secret-key-here
```

### 2. 生产环境建议
- 使用更复杂的密码
- 使用强随机会话密钥
- 考虑使用数据库存储用户信息
- 启用HTTPS传输

### 3. 密码修改
如需修改密码，编辑`utils/auth.py`文件中的：
```python
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("新密码".encode()).hexdigest()
```

## API端点

### 认证相关API
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出  
- `GET /api/auth/status` - 检查认证状态

### 受保护的API
- `POST /api/generate` - 代码生成
- `GET /api/stream/<session_id>` - 消息流
- `POST /api/user_input` - 用户输入
- `POST /api/approve` - 代码审批
- `GET /api/status/<session_id>` - 会话状态

## 测试访问

### 通过Nginx访问
- 登录页面: `https://xpuai.20140806.xyz/autogen/login`
- 主应用: `https://xpuai.20140806.xyz/autogen/`

### 直接访问
- 登录页面: `http://192.168.0.4:5011/login`
- 主应用: `http://192.168.0.4:5011/`

## 故障排除

### 常见问题
1. **无法登录**: 检查用户名和密码是否正确
2. **会话过期**: 重新登录即可
3. **页面不跳转**: 检查JavaScript是否启用
4. **API错误**: 检查网络连接和服务器状态

### 日志查看
应用日志会记录登录成功/失败信息，可用于调试和安全监控。