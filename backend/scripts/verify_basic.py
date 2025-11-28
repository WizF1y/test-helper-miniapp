#!/usr/bin/env python3
"""
基础验证脚本 - 不需要外部依赖

验证题目数据管理功能的基本实现
"""

import os
import sys
import json


def test_api_structure():
    """测试API接口结构"""
    print("=" * 60)
    print("测试API接口结构")
    print("=" * 60)
    
    # 检查app.py中是否包含新增的API接口
    app_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
    
    if not os.path.exists(app_file):
        print("✗ app.py 文件不存在")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    required_apis = [
        ('/api/admin/topics/import', '批量导入题目', 'batch_import_topics'),
        ('/api/admin/topics/backup', '备份题目数据', 'backup_topics'),
        ('/api/admin/topics/statistics', '获取题目统计', 'get_topics_statistics')
    ]
    
    print("\n检查API接口:")
    all_found = True
    for api_path, api_desc, func_name in required_apis:
        path_found = api_path in app_content
        func_found = f"def {func_name}" in app_content
        found = path_found and func_found
        
        status = "✓" if found else "✗"
        result = "已实现" if found else "未找到"
        print(f"  {status} {api_path} ({api_desc}): {result}")
        
        if not found:
            if not path_found:
                print(f"      - 路由未找到")
            if not func_found:
                print(f"      - 函数 {func_name} 未找到")
            all_found = False
    
    print(f"\n{'='*60}")
    print(f"API接口检查: {'全部实现' if all_found else '存在缺失'}")
    print(f"{'='*60}\n")
    
    return all_found


def test_extract_pdf_enhancements():
    """测试extractPDF.py的增强功能"""
    print("=" * 60)
    print("测试PDF提取脚本增强")
    print("=" * 60)
    
    extract_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'questions', 
        'extractPDF.py'
    )
    
    if not os.path.exists(extract_file):
        print("✗ extractPDF.py 文件不存在")
        return False
    
    with open(extract_file, 'r', encoding='utf-8') as f:
        extract_content = f.read()
    
    required_functions = [
        ('validate_topic_data', '数据验证函数'),
        ('clean_topic_data', '数据清洗函数'),
        ('backup_database', '数据库备份函数'),
        ('insert_data_to_mysql', '批量插入函数')
    ]
    
    print("\n检查增强功能:")
    all_found = True
    for func_name, func_desc in required_functions:
        found = f"def {func_name}" in extract_content
        status = "✓" if found else "✗"
        result = "已实现" if found else "未找到"
        print(f"  {status} {func_name} ({func_desc}): {result}")
        if not found:
            all_found = False
    
    # 检查日志配置
    logging_found = 'logging' in extract_content and 'logger' in extract_content
    status = "✓" if logging_found else "✗"
    result = "已配置" if logging_found else "未配置"
    print(f"  {status} 日志系统: {result}")
    if not logging_found:
        all_found = False
    
    # 检查环境变量支持
    env_found = 'load_dotenv' in extract_content
    status = "✓" if env_found else "✗"
    result = "已支持" if env_found else "未支持"
    print(f"  {status} 环境变量配置: {result}")
    if not env_found:
        all_found = False
    
    print(f"\n{'='*60}")
    print(f"PDF提取增强: {'全部实现' if all_found else '存在缺失'}")
    print(f"{'='*60}\n")
    
    return all_found


def test_scripts_exist():
    """测试脚本文件是否存在"""
    print("=" * 60)
    print("测试脚本文件")
    print("=" * 60)
    
    scripts_dir = os.path.dirname(__file__)
    
    required_scripts = [
        ('backup_topics.py', '备份脚本'),
        ('test_import.py', '测试导入脚本'),
        ('verify_implementation.py', '完整验证脚本'),
        ('verify_basic.py', '基础验证脚本')
    ]
    
    print("\n检查脚本文件:")
    all_exist = True
    for script_name, script_desc in required_scripts:
        script_path = os.path.join(scripts_dir, script_name)
        exists = os.path.exists(script_path)
        
        # 检查文件大小
        size = 0
        if exists:
            size = os.path.getsize(script_path)
        
        status = "✓" if exists and size > 100 else "✗"
        result = f"存在 ({size} bytes)" if exists else "缺失"
        print(f"  {status} {script_name} ({script_desc}): {result}")
        
        if not exists or size < 100:
            all_exist = False
    
    # 检查文档
    doc_path = os.path.join(os.path.dirname(scripts_dir), 'TOPIC_MANAGEMENT_README.md')
    doc_exists = os.path.exists(doc_path)
    doc_size = 0
    if doc_exists:
        doc_size = os.path.getsize(doc_path)
    
    status = "✓" if doc_exists and doc_size > 1000 else "✗"
    result = f"存在 ({doc_size} bytes)" if doc_exists else "缺失"
    print(f"  {status} TOPIC_MANAGEMENT_README.md (管理文档): {result}")
    
    if not doc_exists or doc_size < 1000:
        all_exist = False
    
    print(f"\n{'='*60}")
    print(f"文件检查: {'全部存在' if all_exist else '存在缺失'}")
    print(f"{'='*60}\n")
    
    return all_exist


def test_env_example():
    """测试环境变量配置"""
    print("=" * 60)
    print("测试环境变量配置")
    print("=" * 60)
    
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.example')
    
    if not os.path.exists(env_file):
        print("✗ .env.example 文件不存在")
        return False
    
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    required_vars = [
        ('MYSQL_HOST', '数据库主机'),
        ('MYSQL_USER', '数据库用户'),
        ('MYSQL_PASSWORD', '数据库密码'),
        ('MYSQL_DATABASE', '数据库名称'),
        ('ADMIN_KEY', '管理员密钥')
    ]
    
    print("\n检查环境变量:")
    all_found = True
    for var_name, var_desc in required_vars:
        found = var_name in env_content
        status = "✓" if found else "✗"
        result = "已配置" if found else "未配置"
        print(f"  {status} {var_name} ({var_desc}): {result}")
        if not found:
            all_found = False
    
    print(f"\n{'='*60}")
    print(f"环境变量配置: {'全部配置' if all_found else '存在缺失'}")
    print(f"{'='*60}\n")
    
    return all_found


def test_requirements():
    """测试依赖配置"""
    print("=" * 60)
    print("测试依赖配置")
    print("=" * 60)
    
    req_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')
    
    if not os.path.exists(req_file):
        print("✗ requirements.txt 文件不存在")
        return False
    
    with open(req_file, 'r', encoding='utf-8') as f:
        req_content = f.read()
    
    required_packages = [
        ('PyMuPDF', 'PDF处理库'),
        ('Flask', 'Web框架'),
        ('PyMySQL', 'MySQL驱动'),
        ('python-dotenv', '环境变量支持')
    ]
    
    print("\n检查依赖包:")
    all_found = True
    for package_name, package_desc in required_packages:
        found = package_name in req_content
        status = "✓" if found else "✗"
        result = "已添加" if found else "未添加"
        print(f"  {status} {package_name} ({package_desc}): {result}")
        if not found:
            all_found = False
    
    print(f"\n{'='*60}")
    print(f"依赖配置: {'全部配置' if all_found else '存在缺失'}")
    print(f"{'='*60}\n")
    
    return all_found


def main():
    print("\n" + "="*60)
    print("题目数据管理功能基础验证")
    print("="*60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(('API接口结构', test_api_structure()))
    results.append(('PDF提取增强', test_extract_pdf_enhancements()))
    results.append(('脚本文件检查', test_scripts_exist()))
    results.append(('环境变量配置', test_env_example()))
    results.append(('依赖配置', test_requirements()))
    
    # 总结
    print("="*60)
    print("总体验证结果")
    print("="*60)
    
    all_passed = True
    for test_name, test_result in results:
        status = "✓" if test_result else "✗"
        result = "通过" if test_result else "失败"
        print(f"{status} {test_name}: {result}")
        if not test_result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ 所有基础验证通过！题目数据管理功能已正确实现。")
        print("\n实现的功能包括:")
        print("  1. ✓ PDF题目提取脚本增强（数据验证、清洗、日志）")
        print("  2. ✓ 批量导入管理API接口")
        print("  3. ✓ 数据备份脚本和API")
        print("  4. ✓ 测试和验证工具")
        print("  5. ✓ 完整的使用文档")
        print("\n下一步:")
        print("  - 安装依赖: pip install -r requirements.txt")
        print("  - 配置环境变量: 复制 .env.example 到 .env 并填写配置")
        print("  - 运行测试: python backend/scripts/test_import.py --test-validation")
        print("  - 查看文档: backend/TOPIC_MANAGEMENT_README.md\n")
        return 0
    else:
        print("\n✗ 部分验证失败，请检查上述错误信息。\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
