"""
JWT认证中间件
提供token验证装饰器，用于保护需要认证的API接口
"""

from functools import wraps
from flask import request, jsonify
import jwt
import os


def token_required(f):
    """
    JWT认证装饰器
    验证请求头中的Authorization token
    如果验证成功，将user_id添加到request对象中
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                'code': 401,
                'message': '缺少认证token'
            }), 401
        
        try:
            # 移除 "Bearer " 前缀（如果存在）
            if token.startswith('Bearer '):
                token = token[7:]
            
            # 验证token
            secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_development')
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # 将用户信息添加到请求上下文
            request.user_id = data['user_id']
            request.openid = data.get('openid')
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                'message': 'Token已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                'message': '无效的token'
            }), 401
        except Exception as e:
            return jsonify({
                'code': 401,
                'message': f'Token验证失败: {str(e)}'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated


def optional_token(f):
    """
    可选的JWT认证装饰器
    如果提供了token则验证，但不强制要求
    用于某些既可以匿名访问也可以登录访问的接口
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if token:
            try:
                # 移除 "Bearer " 前缀（如果存在）
                if token.startswith('Bearer '):
                    token = token[7:]
                
                # 验证token
                secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_development')
                data = jwt.decode(token, secret_key, algorithms=['HS256'])
                
                # 将用户信息添加到请求上下文
                request.user_id = data['user_id']
                request.openid = data.get('openid')
            except:
                # 如果token无效，不设置user_id，但继续执行
                request.user_id = None
                request.openid = None
        else:
            request.user_id = None
            request.openid = None
        
        return f(*args, **kwargs)
    
    return decorated
