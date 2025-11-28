from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import datetime
import os
import logging
import json
import random
import requests
import hashlib
import jwt
from middleware.auth import token_required, optional_token

# 加载环境变量
load_dotenv()

# 初始化 Flask 应用
app = Flask(__name__)

# 配置日志系统
from config.logging import setup_logging
setup_logging(app)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(
    os.environ.get('MYSQL_USER', 'root'),
    os.environ.get('MYSQL_PASSWORD', ''),
    os.environ.get('MYSQL_HOST', 'localhost'), # docker - mysql
    os.environ.get('MYSQL_DATABASE', 'sz_exam')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义数据模型
class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    openid = db.Column(db.String(64), unique=True, nullable=False)
    nickname = db.Column(db.String(64))
    avatar_url = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    last_login = db.Column(db.DateTime, default=datetime.datetime.now)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, nullable=False)  # 1-单选，2-多选，3-判断
    options = db.Column(db.Text)  # JSON格式存储选项
    answer = db.Column(db.String(16), nullable=False)
    analysis = db.Column(db.Text)
    category_id = db.Column(db.Integer)
    region = db.Column(db.String(32))
    month = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class UserMistake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    user = db.relationship('User', backref=db.backref('mistakes', lazy=True))
    topic = db.relationship('Topic', backref=db.backref('mistakes', lazy=True))

class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    topic = db.relationship('Topic', backref=db.backref('favorites', lazy=True))

class ExamRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_count = db.Column(db.Integer, nullable=False)
    wrong_count = db.Column(db.Integer, nullable=False)
    used_time = db.Column(db.Integer, nullable=False)  # 秒数
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    user = db.relationship('User', backref=db.backref('exam_records', lazy=True))

class ExamDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_record_id = db.Column(db.Integer, db.ForeignKey('exam_record.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    user_answer = db.Column(db.String(16))
    is_correct = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    exam_record = db.relationship('ExamRecord', backref=db.backref('details', lazy=True))
    topic = db.relationship('Topic', backref=db.backref('exam_details', lazy=True))

class UserTopicProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    user = db.relationship('User', backref=db.backref('topic_progress', lazy=True))
    topic = db.relationship('Topic', backref=db.backref('user_progress', lazy=True))


# 全局错误处理器
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    
    if isinstance(e, jwt.ExpiredSignatureError):
        return jsonify({'code': 401, 'message': 'Token已过期'}), 401
    elif isinstance(e, jwt.InvalidTokenError):
        return jsonify({'code': 401, 'message': '无效的token'}), 401
    elif isinstance(e, ValueError):
        return jsonify({'code': 400, 'message': str(e)}), 400
    else:
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'code': 404, 'message': '资源不存在'}), 404

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"Internal error: {str(e)}")
    return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

# 用户登录接口
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        app.logger.info(f"Login request data: {data}")
        code = data.get('code')
        user_info = data.get('userInfo', {})
        
        # 检查是否为调试模式
        debug_mode = os.environ.get('DEBUG_MODE', '').lower() == 'true'
        debug_openid = os.environ.get('DEBUG_OPENID')
        
        if debug_mode and debug_openid:
            # 调试模式，使用固定的 openid
            openid = debug_openid
            app.logger.info("Using debug mode with fixed openid")
        else:
            # 生产模式或非调试模式，调用微信接口
            # 从环境变量获取微信小程序的 AppID 和 AppSecret
            appid = os.environ.get('WECHAT_APPID')
            secret = os.environ.get('WECHAT_SECRET')
            
            if not appid or not secret:
                app.logger.error("Missing WECHAT_APPID or WECHAT_SECRET in environment variables")
                return jsonify({
                    'code': 1,
                    'message': '服务器配置错误'
                }), 500
            
            # 检查是否提供了 code
            if not code:
                app.logger.error("Missing code in request")
                return jsonify({
                    'code': 1,
                    'message': '缺少登录凭证'
                }), 400
            
            # 调用微信接口获取 openid
            wechat_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code"
            response = requests.get(wechat_url)
            wechat_data = response.json()
            
            app.logger.info(f"WeChat API response: {wechat_data}")
            
            if 'errcode' in wechat_data:
                app.logger.error(f"WeChat API error: {wechat_data}")
                return jsonify({
                    'code': 1,
                    'message': '微信登录失败',
                    'error': wechat_data.get('errmsg')
                }), 400
            
            openid = wechat_data.get('openid')
            session_key = wechat_data.get('session_key')
            if not openid:
                app.logger.error("Failed to get openid from WeChat")
                return jsonify({
                    'code': 1,
                    'message': '获取用户信息失败'
                }), 500
        
        # 查找或创建用户
        user = db.session.query(User).filter_by(openid=openid).first()
        if not user:
            user = User(
                openid=openid,
                nickname=user_info.get('nickName', '用户'),
                avatar_url=user_info.get('avatarUrl', '')
            )
            db.session.add(user)
            db.session.flush()  # 获取 user.id
        else:
            user.last_login = datetime.datetime.now()
            if user_info.get('nickName'):
                user.nickname = user_info.get('nickName')
            if user_info.get('avatarUrl'):
                user.avatar_url = user_info.get('avatarUrl')
        
        # 生成自定义登录态 token
        token_data = {
            'user_id': user.id,
            'openid': openid,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)  # 7天过期
        }
        
        # 使用 SECRET_KEY 作为 JWT 密钥
        secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_development')
        token = jwt.encode(token_data, secret_key, algorithm='HS256')
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '登录成功',
            'data': {
                'userId': user.id,
                'token': token,
                'nickname': user.nickname,
                'avatarUrl': user.avatar_url
            }
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '登录失败',
            'error': str(e)
        }), 500

# 获取题目列表
@app.route('/api/topics', methods=['GET'])
def get_topics():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    type_id = request.args.get('type', type=int)
    month = request.args.get('month', type=int)
    region = request.args.get('region')
    user_id = request.args.get('userId', type=int)
    exclude_answered = request.args.get('excludeAnswered', False, type=bool)
    
    query = db.session.query(Topic)
    
    if type_id:
        query = query.filter_by(type_id=type_id)
    if month:
        query = query.filter_by(month=month)
    if region:
        query = query.filter_by(region=region)
    
    # 如果需要排除用户已答题目
    if exclude_answered and user_id:
        # 使用 select() 构造来避免 SQLAlchemy 警告
        from sqlalchemy import select
        answered_subquery = select(UserTopicProgress.topic_id).where(
            UserTopicProgress.user_id == user_id
        ).scalar_subquery()
        query = query.filter(~Topic.id.in_(answered_subquery))
    
    total = query.count()
    topics = query.order_by(Topic.id.desc()).paginate(page=page, per_page=size, error_out=False)
    
    result = []
    for topic in topics.items:
        result.append({
            'id': topic.id,
            'content': topic.content,
            'type': topic.type_id,
            'options': json.loads(topic.options),
            'answer': topic.answer,
            'analysis': topic.analysis
        })
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'total': total,
            'list': result,
            'page': page,
            'size': size
        }
    })

# 随机获取题目
@app.route('/api/exam/random', methods=['GET'])
def get_random_exam():
    count = request.args.get('count', 20, type=int)
    
    # 随机获取题目
    topics = db.session.query(Topic).order_by(db.func.random()).limit(count).all()
    
    result = []
    for topic in topics:
        result.append({
            'id': topic.id,
            'content': topic.content,
            'type': topic.type_id,
            'options': json.loads(topic.options),
            'answer': topic.answer
        })
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': result
    })

# 随机练习 - 根据月份范围获取题目
@app.route('/api/topics/random', methods=['GET'])
def get_random_topics():
    # 支持两种参数格式
    # 1. months: 逗号分隔的月份列表，例如 "8,10,11"
    # 2. startMonth, endMonth: 月份范围
    months_param = request.args.get('months')
    start_month = request.args.get('startMonth', type=int)
    end_month = request.args.get('endMonth', type=int)
    count = request.args.get('count', 20, type=int)
    user_id = request.args.get('userId', type=int)
    
    # 构建查询
    query = db.session.query(Topic)
    
    # 优先使用 months 参数
    if months_param:
        # 解析月份列表
        months = [int(m) for m in months_param.split(',') if m.isdigit()]
        if months:
            query = query.filter(Topic.month.in_(months))
    # 否则使用月份范围
    elif start_month and end_month:
        if start_month <= end_month:
            query = query.filter(Topic.month >= start_month, Topic.month <= end_month)
        else:
            # 处理跨年情况，例如11月到2月
            query = query.filter(db.or_(Topic.month >= start_month, Topic.month <= end_month))
    elif start_month:
        query = query.filter(Topic.month >= start_month)
    elif end_month:
        query = query.filter(Topic.month <= end_month)
    
    # 随机获取指定数量的题目
    topics = query.order_by(db.func.random()).limit(count).all()
    
    result = []
    for topic in topics:
        result.append({
            'id': topic.id,
            'content': topic.content,
            'type': topic.type_id,
            'options': json.loads(topic.options) if topic.options else [],
            'answer': topic.answer,
            'analysis': topic.analysis,
            'month': topic.month
        })
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': result
    })

# 提交考试结果
@app.route('/api/exam/submit', methods=['POST'])
@token_required
def submit_exam():
    data = request.json
    # 从token中获取user_id（已经是整数类型）
    user_id = request.user_id
    score = data.get('score')
    total_questions = data.get('totalQuestions')
    correct_count = data.get('correctCount')
    wrong_count = data.get('wrongCount')
    used_time = data.get('usedTime')
    details = data.get('details', [])  # 答题详情列表
    
    try:
        # 创建考试记录
        record = ExamRecord(
            user_id=user_id,
            score=score,
            total_questions=total_questions,
            correct_count=correct_count,
            wrong_count=wrong_count,
            used_time=used_time
        )
        db.session.add(record)
        db.session.flush()  # 获取 record.id
        
        # 保存每道题的答题详情
        for detail in details:
            exam_detail = ExamDetail(
                exam_record_id=record.id,
                topic_id=detail.get('topicId'),
                user_answer=detail.get('userAnswer'),
                is_correct=detail.get('isCorrect')
            )
            db.session.add(exam_detail)
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '提交成功',
            'data': {
                'recordId': record.id
            }
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Submit exam error: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '提交失败',
            'error': str(e)
        }), 500

# 获取考试详情
@app.route('/api/exam/detail/<int:record_id>', methods=['GET'])
def get_exam_detail(record_id):
    try:
        # 获取考试记录
        record = db.session.get(ExamRecord, record_id)
        if not record:
            return jsonify({
                'code': 1,
                'message': '考试记录不存在'
            }), 404
        
        # 获取答题详情
        details = db.session.query(ExamDetail).filter_by(exam_record_id=record_id).all()
        
        detail_list = []
        for detail in details:
            topic = detail.topic
            detail_list.append({
                'topicId': topic.id,
                'content': topic.content,
                'type': topic.type_id,
                'options': json.loads(topic.options) if topic.options else [],
                'correctAnswer': topic.answer,
                'userAnswer': detail.user_answer,
                'isCorrect': detail.is_correct,
                'analysis': topic.analysis
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'recordId': record.id,
                'score': record.score,
                'totalQuestions': record.total_questions,
                'correctCount': record.correct_count,
                'wrongCount': record.wrong_count,
                'usedTime': record.used_time,
                'createdAt': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'details': detail_list
            }
        })
    except Exception as e:
        app.logger.error(f"Get exam detail error: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取失败',
            'error': str(e)
        }), 500

# 添加错题
@app.route('/api/mistake/add', methods=['POST'])
@token_required
def add_mistake():
    data = request.json
    # 从token中获取user_id
    user_id = request.user_id
    topic_id = data.get('topicId')
    
    # 确保topic_id为整数类型
    try:
        topic_id = int(topic_id)
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'message': '参数类型错误'})
    
    # 检查是否已存在
    exists = db.session.query(UserMistake).filter_by(user_id=user_id, topic_id=topic_id).first()
    if exists:
        return jsonify({
            'code': 0,
            'message': '该题目已在错题本中'
        })
    
    # 添加错题记录
    try:
        mistake = UserMistake(user_id=user_id, topic_id=topic_id)
        db.session.add(mistake)
        db.session.commit()
        return jsonify({
            'code': 0,
            'message': '添加成功'
        })
    except Exception as e:
        db.session.rollback()
        # 如果是重复键错误，返回成功（因为记录已存在）
        if 'Duplicate entry' in str(e):
            app.logger.warning(f'错题已存在: user_id={user_id}, topic_id={topic_id}')
            return jsonify({
                'code': 0,
                'message': '该题目已在错题本中'
            })
        # 其他错误则抛出
        app.logger.error(f'添加错题失败: {str(e)}')
        return jsonify({'code': 1, 'message': '添加失败'}), 500

# 获取错题列表
@app.route('/api/mistake/list', methods=['GET'])
@token_required
def get_mistakes():
    # 从token中获取user_id
    user_id = request.user_id
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    month = request.args.get('month', type=int)
    type_id = request.args.get('type', type=int)
    sort_by = request.args.get('sortBy', 'time')  # time-时间, frequency-错误次数
    
    # 构建查询，联表查询Topic
    query = db.session.query(UserMistake).filter_by(user_id=user_id).join(Topic)
    
    # 月份筛选
    if month:
        query = query.filter(Topic.month == month)
    
    # 题型筛选
    if type_id:
        query = query.filter(Topic.type_id == type_id)
    
    total = query.count()
    
    # 排序
    if sort_by == 'frequency':
        # 按错误次数排序（暂时按创建时间，后续可扩展）
        query = query.order_by(UserMistake.created_at.desc())
    else:
        # 默认按时间排序
        query = query.order_by(UserMistake.created_at.desc())
    
    mistakes = query.paginate(page=page, per_page=size, error_out=False)
    
    result = []
    for mistake in mistakes.items:
        topic = mistake.topic
        result.append({
            'id': topic.id,  # 使用 topic.id 作为主键，保持与其他接口一致
            'content': topic.content,
            'type': topic.type_id,
            'options': json.loads(topic.options),
            'answer': topic.answer,
            'analysis': topic.analysis,
            'month': topic.month,
            'region': topic.region,
            'createdAt': mistake.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'total': total,
            'list': result,
            'page': page,
            'size': size
        }
    })

# 获取错题统计
@app.route('/api/mistake/statistics', methods=['GET'])
@token_required
def get_mistake_statistics():
    # 从token中获取user_id
    user_id = request.user_id
    
    # 总错题数
    total_count = db.session.query(UserMistake).filter_by(user_id=user_id).count()
    
    # 按题型统计
    by_type = {}
    type_stats = db.session.query(
        Topic.type_id,
        db.func.count(UserMistake.id)
    ).join(UserMistake).filter(
        UserMistake.user_id == user_id
    ).group_by(Topic.type_id).all()
    
    for type_id, count in type_stats:
        by_type[str(type_id)] = count
    
    # 按月份统计
    by_month = {}
    month_stats = db.session.query(
        Topic.month,
        db.func.count(UserMistake.id)
    ).join(UserMistake).filter(
        UserMistake.user_id == user_id
    ).group_by(Topic.month).all()
    
    for month, count in month_stats:
        if month:  # 排除month为None的情况
            by_month[str(month)] = count
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'totalCount': total_count,
            'byType': by_type,
            'byMonth': by_month
        }
    })

# 删除错题
@app.route('/api/mistake/delete', methods=['POST'])
@token_required
def delete_mistake():
    data = request.json
    # 从token中获取user_id
    user_id = request.user_id
    topic_id = data.get('topicId')
    
    # 确保topic_id为整数类型
    try:
        topic_id = int(topic_id)
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'message': '参数类型错误'})
    
    db.session.query(UserMistake).filter_by(user_id=user_id, topic_id=topic_id).delete()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '删除成功'
    })

# 清空错题
@app.route('/api/mistake/clear', methods=['POST'])
@token_required
def clear_mistakes():
    # 从token中获取user_id（已经是整数类型）
    user_id = request.user_id
    
    db.session.query(UserMistake).filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '清空成功'
    })

# 添加收藏
@app.route('/api/favorite/add', methods=['POST'])
@token_required
def add_favorite():
    data = request.json
    # 从token中获取user_id
    user_id = request.user_id
    topic_id = data.get('topicId')
    
    # 确保topic_id为整数类型
    try:
        topic_id = int(topic_id)
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'message': '参数类型错误'})
    
    # 检查是否已存在
    exists = UserFavorite.query.filter_by(user_id=user_id, topic_id=topic_id).first()
    if exists:
        return jsonify({
            'code': 0,
            'message': '该题目已收藏'
        })
    
    # 添加收藏记录
    favorite = UserFavorite(user_id=user_id, topic_id=topic_id)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '收藏成功'
    })

# 获取收藏列表
@app.route('/api/favorite/list', methods=['GET'])
@token_required
def get_favorites():
    # 从token中获取user_id
    user_id = request.user_id
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    query = UserFavorite.query.filter_by(user_id=user_id)
    total = query.count()
    
    favorites = query.order_by(UserFavorite.created_at.desc()).paginate(page=page, per_page=size, error_out=False)
    
    result = []
    for favorite in favorites.items:
        topic = favorite.topic
        result.append({
            'id': topic.id,  # 使用 topic.id 作为主键，保持与其他接口一致
            'content': topic.content,
            'type': topic.type_id,
            'options': json.loads(topic.options),
            'answer': topic.answer,
            'analysis': topic.analysis,
            'month': topic.month,
            'region': topic.region,
            'createdAt': favorite.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'total': total,
            'list': result,
            'page': page,
            'size': size
        }
    })

# 取消收藏
@app.route('/api/favorite/delete', methods=['POST'])
@token_required
def delete_favorite():
    data = request.json
    # 从token中获取user_id
    user_id = request.user_id
    topic_id = data.get('topicId')
    
    # 确保topic_id为整数类型
    try:
        topic_id = int(topic_id)
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'message': '参数类型错误'})
    
    UserFavorite.query.filter_by(user_id=user_id, topic_id=topic_id).delete()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '取消收藏成功'
    })

# 清空收藏
@app.route('/api/favorite/clear', methods=['POST'])
@token_required
def clear_favorites():
    # 从token中获取user_id（已经是整数类型）
    user_id = request.user_id
    
    UserFavorite.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({
        'code': 0,
        'message': '清空成功'
    })

# 获取用户统计信息
@app.route('/api/user/statistics', methods=['GET'])
@token_required
def get_user_statistics():
    # 从token中获取user_id，优先使用token中的用户ID
    user_id = request.user_id
    # 如果请求参数中也提供了userId，验证是否匹配
    param_user_id = request.args.get('userId', type=int)
    if param_user_id and param_user_id != user_id:
        return jsonify({
            'code': 403,
            'message': '无权访问其他用户的数据'
        }), 403
    
    # 获取错题数量
    mistake_count = UserMistake.query.filter_by(user_id=user_id).count()
    
    # 获取收藏数量
    favorite_count = UserFavorite.query.filter_by(user_id=user_id).count()
    
    # # 获取考试记录
    # exam_records = ExamRecord.query.filter_by(user_id=user_id).order_by(ExamRecord.created_at.desc()).limit(5).all()
    
    # records = []
    # for record in exam_records:
    #     records.append({
    #         'id': record.id,
    #         'score': record.score,
    #         'totalQuestions': record.total_questions,
    #         'correctCount': record.correct_count,
    #         'wrongCount': record.wrong_count,
    #         'usedTime': record.used_time,
    #         'createdAt': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
    #     })
    
    # 计算做题总数（包括考试中的题目）
    done_count = db.session.query(db.func.count(UserTopicProgress.topic_id)).filter_by(user_id=user_id).scalar() or 0
    
    # 计算用户使用天数
    user = db.session.get(User, user_id)
    if user:
        days_count = (datetime.datetime.now() - user.created_at).days + 1
    else:
        days_count = 1
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'mistakeCount': mistake_count,
            'favoriteCount': favorite_count,
            'doneCount': done_count,
            'daysCount': days_count
        }
    })

# 获取每月题目数量
@app.route('/api/topics/count-by-month', methods=['GET'])
def get_topics_count_by_month():
    # 获取请求的月份列表
    months_param = request.args.get('months', '')
    if months_param:
        months = [int(m) for m in months_param.split(',') if m.isdigit()]
    else:
        # 如果未提供月份，则获取所有月份的数据
        months = list(range(1, 13))
    
    result = []
    for month in months:
        # 获取该月的题目数量
        count = Topic.query.filter_by(month=month).count()
        result.append({
            'month': month,
            'count': count
        })
    
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': result
    })

# 获取每月做题进度
@app.route('/api/user/month-progress', methods=['GET'])
@token_required
def get_month_progress():
    # 从token中获取user_id
    user_id = request.user_id
    # 获取请求的月份列表
    months_param = request.args.get('months', '')
    if months_param:
        months = [int(m) for m in months_param.split(',') if m.isdigit()]
    else:
        # 如果未提供月份，则获取所有月份的数据
        months = list(range(1, 13))
    
    result = []
    for month in months:
        # 通过查询 UserTopicProgress 表统计用户该月完成的题目数
        completed_count = db.session.query(UserTopicProgress).filter(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.month == month
        ).count()
        
        result.append({
            'month': month,
            'completedCount': completed_count
        })

    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': result
    })

# 用户完成题目接口
@app.route('/api/progress/finish-topic', methods=['POST'])
@token_required
def finish_topic():
    data = request.json
    # 从token中获取user_id（已经是整数类型）
    user_id = request.user_id
    topic_id = data.get('topicId')
    month = data.get('month')

    # 参数存在性检查
    if topic_id is None or month is None:
        return jsonify({'code': 1, 'message': '参数缺失'})

    # 参数类型检查和转换
    try:
        topic_id = int(topic_id)
        month = int(month)
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'message': '参数类型错误'})

    # 检查用户是否存在
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'code': 1, 'message': '用户不存在'})

    # 检查题目是否存在
    topic = db.session.get(Topic, topic_id)
    if not topic:
        return jsonify({'code': 1, 'message': '题目不存在'})

    # 检查是否已存在记录
    exists = UserTopicProgress.query.filter_by(user_id=user_id, topic_id=topic_id, month=month).first()
    if exists:
        return jsonify({'code': 0, 'message': '已记录完成'})

    # 新增完成记录
    try:
        progress = UserTopicProgress(user_id=user_id, topic_id=topic_id, month=month)
        db.session.add(progress)
        db.session.commit()
        return jsonify({'code': 0, 'message': '记录完成'})
    except Exception as e:
        db.session.rollback()
        # 如果是重复键错误，返回成功（因为记录已存在）
        if 'Duplicate entry' in str(e):
            app.logger.warning(f'题目进度已存在: user_id={user_id}, topic_id={topic_id}, month={month}')
            return jsonify({'code': 0, 'message': '已记录完成'})
        # 其他错误则抛出
        app.logger.error(f'记录题目进度失败: {str(e)}')
        return jsonify({'code': 1, 'message': '记录失败'}), 500

# 管理接口：批量导入题目
@app.route('/api/admin/topics/import', methods=['POST'])
def batch_import_topics():
    """
    批量导入题目数据
    支持JSON格式的题目列表
    """
    try:
        # 验证管理员权限（简单实现，可以后续增强）
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('ADMIN_KEY', 'default_admin_key'):
            return jsonify({
                'code': 403,
                'message': '无权限访问'
            }), 403
        
        data = request.json
        topics = data.get('topics', [])
        
        if not topics or not isinstance(topics, list):
            return jsonify({
                'code': 400,
                'message': '题目数据格式错误'
            }), 400
        
        inserted_count = 0
        skipped_count = 0
        error_list = []
        
        for i, topic_data in enumerate(topics):
            try:
                # 验证数据
                required_fields = ['content', 'type_id', 'options', 'answer']
                for field in required_fields:
                    if field not in topic_data:
                        error_list.append(f"题目{i+1}缺少字段: {field}")
                        skipped_count += 1
                        continue
                
                # 检查是否重复
                exists = Topic.query.filter_by(
                    content=topic_data['content'],
                    month=topic_data.get('month')
                ).first()
                
                if exists:
                    skipped_count += 1
                    continue
                
                # 创建题目
                topic = Topic(
                    content=topic_data['content'],
                    type_id=topic_data['type_id'],
                    options=json.dumps(topic_data['options'], ensure_ascii=False),
                    answer=topic_data['answer'],
                    analysis=topic_data.get('analysis'),
                    category_id=topic_data.get('category_id'),
                    region=topic_data.get('region'),
                    month=topic_data.get('month')
                )
                
                db.session.add(topic)
                inserted_count += 1
                
                # 每100条提交一次
                if inserted_count % 100 == 0:
                    db.session.commit()
                    app.logger.info(f"已导入 {inserted_count} 条题目")
                
            except Exception as e:
                error_list.append(f"题目{i+1}导入失败: {str(e)}")
                skipped_count += 1
                continue
        
        # 最后提交剩余的
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '导入完成',
            'data': {
                'inserted': inserted_count,
                'skipped': skipped_count,
                'errors': error_list[:10]  # 只返回前10个错误
            }
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Batch import error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '导入失败',
            'error': str(e)
        }), 500

# 管理接口：备份题目数据
@app.route('/api/admin/topics/backup', methods=['GET'])
def backup_topics():
    """
    导出所有题目数据为JSON格式
    """
    try:
        # 验证管理员权限
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('ADMIN_KEY', 'default_admin_key'):
            return jsonify({
                'code': 403,
                'message': '无权限访问'
            }), 403
        
        # 查询所有题目
        topics = Topic.query.all()
        
        backup_data = []
        for topic in topics:
            backup_data.append({
                'id': topic.id,
                'content': topic.content,
                'type_id': topic.type_id,
                'options': json.loads(topic.options) if topic.options else [],
                'answer': topic.answer,
                'analysis': topic.analysis,
                'category_id': topic.category_id,
                'region': topic.region,
                'month': topic.month,
                'created_at': topic.created_at.strftime('%Y-%m-%d %H:%M:%S') if topic.created_at else None
            })
        
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'topics_backup_{timestamp}.json'
        
        return jsonify({
            'code': 0,
            'message': '备份成功',
            'data': {
                'filename': filename,
                'total': len(backup_data),
                'topics': backup_data
            }
        })
        
    except Exception as e:
        app.logger.error(f"Backup error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '备份失败',
            'error': str(e)
        }), 500

# 管理接口：获取题目统计信息
@app.route('/api/admin/topics/statistics', methods=['GET'])
def get_topics_statistics():
    """
    获取题目数据统计信息
    """
    try:
        # 验证管理员权限
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('ADMIN_KEY', 'default_admin_key'):
            return jsonify({
                'code': 403,
                'message': '无权限访问'
            }), 403
        
        # 总题目数
        total_count = Topic.query.count()
        
        # 按题型统计
        by_type = {}
        type_stats = db.session.query(
            Topic.type_id,
            db.func.count(Topic.id)
        ).group_by(Topic.type_id).all()
        
        for type_id, count in type_stats:
            by_type[str(type_id)] = count
        
        # 按月份统计
        by_month = {}
        month_stats = db.session.query(
            Topic.month,
            db.func.count(Topic.id)
        ).group_by(Topic.month).all()
        
        for month, count in month_stats:
            if month:
                by_month[str(month)] = count
        
        # 按地区统计
        by_region = {}
        region_stats = db.session.query(
            Topic.region,
            db.func.count(Topic.id)
        ).filter(Topic.region.isnot(None)).group_by(Topic.region).all()
        
        for region, count in region_stats:
            by_region[region] = count
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'totalCount': total_count,
                'byType': by_type,
                'byMonth': by_month,
                'byRegion': by_region
            }
        })
        
    except Exception as e:
        app.logger.error(f"Statistics error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '获取失败',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=True)
