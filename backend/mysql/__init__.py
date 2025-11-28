from flask import Flask
from . import database

# 导出关键组件，使外部可以直接从mysql包导入
from .database import get_db, close_db, init_db_command

def init_app(app=None):
    """初始化MySQL数据库与Flask应用的集成"""
    if app is None:
        app = Flask(__name__)
        
        # 加载MySQL配置
        app.config.from_mapping(
            MYSQL_HOST='127.0.0.1',
            MYSQL_USER='root',     
            MYSQL_PASSWORD='',     
            MYSQL_DB='sz_exam'       
        )
    
    # 初始化数据库模块
    database.init_app(app)
    
    return app

def create_app():
    """创建并返回配置好的Flask应用"""
    app = Flask(__name__)

    # 加载MySQL配置
    app.config.from_mapping(
        # SECRET_KEY='dev',
        MYSQL_HOST='127.0.0.1',
        MYSQL_USER='root',     
        MYSQL_PASSWORD='',     
        MYSQL_DB='sz_exam'       
    )
    
    # 初始化数据库
    init_app(app)
    
    return app

# 可以保留create_tables函数作为API，但移除直接运行的部分
def create_tables():
    """创建所有必要的数据库表（推荐使用 flask init-db 命令替代）"""
    app = create_app()
    with app.app_context():
        database.init_db()