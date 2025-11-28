#!/usr/bin/env python3
"""
题目数据备份脚本

用法:
    python backup_topics.py                    # 备份到默认目录
    python backup_topics.py --output /path     # 备份到指定目录
    python backup_topics.py --format sql       # 导出为SQL格式
"""

import os
import sys
import json
import argparse
from datetime import datetime

# 添加父目录到路径以便导入app模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from mysql import connector

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'sz_exam')
}


def backup_to_json(output_dir='backups'):
    """
    备份题目数据到JSON文件
    
    Args:
        output_dir: 输出目录
        
    Returns:
        str: 备份文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(output_dir, f'topics_backup_{timestamp}.json')
    
    conn = None
    cursor = None
    
    try:
        print(f"连接数据库: {DB_CONFIG['database']}@{DB_CONFIG['host']}...")
        conn = connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有题目
        print("正在查询题目数据...")
        cursor.execute("SELECT * FROM topic ORDER BY id")
        topics = cursor.fetchall()
        
        # 转换日期时间为字符串
        for topic in topics:
            if 'created_at' in topic and topic['created_at']:
                topic['created_at'] = topic['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            # 解析options字段
            if 'options' in topic and topic['options']:
                try:
                    topic['options'] = json.loads(topic['options'])
                except:
                    pass
        
        # 写入JSON文件
        print(f"正在写入备份文件: {backup_file}...")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                'backup_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(topics),
                'topics': topics
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 备份完成!")
        print(f"  文件路径: {backup_file}")
        print(f"  题目数量: {len(topics)}")
        
        return backup_file
        
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def backup_to_sql(output_dir='backups'):
    """
    备份题目数据到SQL文件
    
    Args:
        output_dir: 输出目录
        
    Returns:
        str: 备份文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(output_dir, f'topics_backup_{timestamp}.sql')
    
    conn = None
    cursor = None
    
    try:
        print(f"连接数据库: {DB_CONFIG['database']}@{DB_CONFIG['host']}...")
        conn = connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有题目
        print("正在查询题目数据...")
        cursor.execute("SELECT * FROM topic ORDER BY id")
        topics = cursor.fetchall()
        
        # 生成SQL语句
        print(f"正在生成SQL语句...")
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"-- 题目数据备份\n")
            f.write(f"-- 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 题目数量: {len(topics)}\n\n")
            f.write(f"USE {DB_CONFIG['database']};\n\n")
            
            for topic in topics:
                # 转义字符串
                content = topic['content'].replace("'", "''") if topic['content'] else ''
                options = topic['options'].replace("'", "''") if topic['options'] else ''
                answer = topic['answer'].replace("'", "''") if topic['answer'] else ''
                analysis = topic['analysis'].replace("'", "''") if topic['analysis'] else ''
                region = topic['region'].replace("'", "''") if topic['region'] else ''
                
                sql = f"INSERT INTO topic (id, content, type_id, options, answer, analysis, category_id, region, month, created_at) VALUES ("
                sql += f"{topic['id']}, "
                sql += f"'{content}', "
                sql += f"{topic['type_id']}, "
                sql += f"'{options}', "
                sql += f"'{answer}', "
                sql += f"'{analysis}' if analysis else 'NULL', "
                sql += f"{topic['category_id'] if topic['category_id'] else 'NULL'}, "
                sql += f"'{region}' if region else 'NULL', "
                sql += f"{topic['month'] if topic['month'] else 'NULL'}, "
                
                if topic['created_at']:
                    created_at = topic['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    sql += f"'{created_at}'"
                else:
                    sql += "NULL"
                
                sql += ");\n"
                f.write(sql)
        
        print(f"✓ 备份完成!")
        print(f"  文件路径: {backup_file}")
        print(f"  题目数量: {len(topics)}")
        
        return backup_file
        
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def main():
    parser = argparse.ArgumentParser(description='题目数据备份工具')
    parser.add_argument('--output', '-o', default='backups', help='输出目录 (默认: backups)')
    parser.add_argument('--format', '-f', choices=['json', 'sql'], default='json', help='备份格式 (默认: json)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("题目数据备份工具")
    print("=" * 60)
    
    if args.format == 'json':
        backup_to_json(args.output)
    else:
        backup_to_sql(args.output)
    
    print("=" * 60)


if __name__ == '__main__':
    main()
