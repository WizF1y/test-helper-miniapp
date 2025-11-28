import pymysql
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """
    获取与MySQL数据库的连接
    g是一个特殊的对象，独立于每一个请求。它会在处理请求中把多个连接、多个函数所用到的数据存储其中，
    反复使用，不需要每次调用该函数都要重新创建新的链接
    """
    if 'db' not in g:
        g.db = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],        # 使用正确的键名 MYSQL_HOST
            user=current_app.config['MYSQL_USER'],        # 使用正确的键名 MYSQL_USER
            password=current_app.config['MYSQL_PASSWORD'], # 使用正确的键名 MYSQL_PASSWORD
            database=current_app.config['MYSQL_DB'],      # 使用正确的键名 MYSQL_DB
            charset='utf8mb4',                           # 字符集
            cursorclass=pymysql.cursors.DictCursor       # 使用字典游标
        )

    return g.db

def close_db(e=None):
    """
    通过检查g.db来确定连接是否已经建立。如果连接已建立，那么就关闭连接。
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    """数据库初始化，创建表"""
    db = get_db()
    cursor = db.cursor()
    
    with current_app.open_resource('init.sql') as f:
        # MySQL需要分割多条SQL语句
        sql_commands = f.read().decode('utf8').split(';')
        for command in sql_commands:
            if command.strip():  # 忽略空命令
                cursor.execute(command)
    
    db.commit()
    cursor.close()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """清除已经存在的表创建新的表"""
    init_db()
    click.echo('数据库初始化已完成')

def init_app(app):
    app.teardown_appcontext(close_db)  # 告诉flask在返回响应后进行清理的时候调用此函数
    app.cli.add_command(init_db_command)  # 添加数据库表初始化命令
