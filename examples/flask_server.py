#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neural Network Playground Blueprint - 用于集成到主应用中
"""

from flask import Blueprint, send_from_directory, send_file, make_response, request, jsonify
import os

# 创建Blueprint实例
nnplayground_bp = Blueprint('nnplayground', __name__)

# 全局变量用于存储认证函数和工具统计函数
_authenticate_user = None
_verify_access_token = None
_user_key_config = None
_increment_tool_visits = None

# 获取当前目录路径
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


def check_auth():
    """检查用户认证"""
    print(f"检查认证: _authenticate_user={_authenticate_user is not None}, _verify_access_token={_verify_access_token is not None}, _user_key_config={_user_key_config is not None}")
    if not _authenticate_user or not _verify_access_token or not _user_key_config:
        return {'error': '认证系统未初始化', 'status': 500}
    
    # 获取认证参数
    user = request.args.get('user') or request.form.get('user')
    key = request.args.get('key') or request.form.get('key')
    token = request.args.get('token') or request.form.get('token')
    
    if not user or not key:
        return {'error': '缺少用户认证参数', 'status': 401}
    
    # 验证用户凭据
    if not _authenticate_user(user, key):
        return {'error': '用户认证失败', 'status': 401}
    
    # 验证访问令牌
    if token and not _verify_access_token(user, token, _user_key_config):
        return {'error': '访问令牌无效', 'status': 401}
    
    return None


@nnplayground_bp.route('/')
def nnplayground_index():
    """主页路由 - 返回index.html"""
    # 记录访问统计
    if _increment_tool_visits:
        _increment_tool_visits('nnplayground')

    auth_result = check_auth()
    if auth_result:
        return jsonify({'success': False, 'message': auth_result['error']}), auth_result.get('status', 401)

    return send_file(os.path.join(STATIC_DIR, 'index.html'))


@nnplayground_bp.route('/bundle.js')
def nnplayground_bundle_js():
    """JavaScript bundle文件路由"""
    auth_result = check_auth()
    if auth_result:
        return jsonify({'success': False, 'message': auth_result['error']}), auth_result.get('status', 401)

    file_path = os.path.join(STATIC_DIR, 'bundle.js')
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "文件未找到", 404

    # 设置正确的MIME类型
    response = make_response(send_file(file_path))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response


@nnplayground_bp.route('/bundle.css')
def nnplayground_bundle_css():
    """CSS bundle文件路由"""
    auth_result = check_auth()
    if auth_result:
        return jsonify({'success': False, 'message': auth_result['error']}), auth_result.get('status', 401)

    file_path = os.path.join(STATIC_DIR, 'bundle.css')
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "文件未找到", 404

    # 设置正确的MIME类型
    response = make_response(send_file(file_path))
    response.headers['Content-Type'] = 'text/css'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response


@nnplayground_bp.route('/lib.js')
def nnplayground_lib_js():
    """库文件路由"""
    auth_result = check_auth()
    if auth_result:
        return jsonify({'success': False, 'message': auth_result['error']}), auth_result.get('status', 401)

    file_path = os.path.join(STATIC_DIR, 'lib.js')
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "文件未找到", 404

    # 设置正确的MIME类型
    response = make_response(send_file(file_path))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response


@nnplayground_bp.route('/analytics.js')
def nnplayground_analytics_js():
    """分析脚本文件路由"""
    auth_result = check_auth()
    if auth_result:
        return jsonify({'success': False, 'message': auth_result['error']}), auth_result.get('status', 401)

    file_path = os.path.join(STATIC_DIR, 'analytics.js')
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "文件未找到", 404

    # 设置正确的MIME类型
    response = make_response(send_file(file_path))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response


@nnplayground_bp.route('/favicon.ico')
def nnplayground_favicon_ico():
    """Favicon.ico路由 - 返回AI助教神经网络主题图标"""
    file_path = os.path.join(STATIC_DIR, 'favicon.ico')
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "图标文件未找到", 404

    # 设置正确的MIME类型
    response = make_response(send_file(file_path))
    response.headers['Content-Type'] = 'image/x-icon'
    response.headers['Cache-Control'] = 'public, max-age=86400'  # 缓存24小时

    return response


@nnplayground_bp.route('/favicon.png')
def nnplayground_favicon_png():
    """Favicon.png路由 - 返回AI助教神经网络主题图标"""
    file_path = os.path.join(STATIC_DIR, 'favicon.png')
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "图标文件未找到", 404

    # 设置正确的MIME类型
    response = make_response(send_file(file_path))
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'public, max-age=86400'  # 缓存24小时

    return response


@nnplayground_bp.route('/<path:filename>')
def nnplayground_static_files(filename):
    """其他静态文件路由"""
    auth_result = check_auth()
    if auth_result:
        return jsonify({'success': False, 'message': auth_result['error']}), auth_result.get('status', 401)

    return send_from_directory(STATIC_DIR, filename)


# 导出Blueprint和初始化函数供主应用使用
def init_nnplayground_bp(authenticate_user_func=None, verify_access_token_func=None, user_key_config_obj=None, increment_tool_visits_func=None):
    """初始化nnplayground blueprint的函数"""
    global _authenticate_user, _verify_access_token, _user_key_config, _increment_tool_visits

    # 设置认证函数
    _authenticate_user = authenticate_user_func
    _verify_access_token = verify_access_token_func
    _user_key_config = user_key_config_obj
    _increment_tool_visits = increment_tool_visits_func

    return nnplayground_bp


if __name__ == '__main__':
    # 如果直接运行此文件，创建一个临时Flask应用用于测试
    from flask import Flask

    # 模拟认证函数用于测试
    def mock_authenticate_user(user, key):
        """模拟用户认证函数"""
        return user == "admin" and key == "admin123"

    def mock_verify_access_token(user, token, config):
        """模拟令牌验证函数"""
        return True  # 测试时总是返回True

    def mock_increment_tool_visits(tool_name):
        """模拟访问统计函数"""
        print(f"访问工具: {tool_name}")

    # 模拟用户配置
    mock_config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'password': 'admin123',
                    'token': 'test_token',
                    'expiry': 9999999999
                }
            }
        }
    }

    # 初始化认证函数
    print("初始化认证函数...")
    init_nnplayground_bp(
        authenticate_user_func=mock_authenticate_user,
        verify_access_token_func=mock_verify_access_token,
        user_key_config_obj=mock_config,
        increment_tool_visits_func=mock_increment_tool_visits
    )
    print("认证函数初始化完成")

    test_app = Flask(__name__)
    test_app.register_blueprint(nnplayground_bp, url_prefix='/nnplayground')

    print("启动Flask测试服务器...")
    print(f"静态文件目录: {STATIC_DIR}")
    print("访问地址: http://localhost:5001/nnplayground")

    # 启动Flask开发服务器（启用调试模式）
    test_app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5001,       # 端口号
        debug=True,      # 启用调试模式查看详细日志
        threaded=True    # 启用多线程
    )
