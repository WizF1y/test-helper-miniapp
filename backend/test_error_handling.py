#!/usr/bin/env python
"""
错误处理和日志系统测试脚本
验证任务11的实施是否正确
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config.logging import setup_logging
import logging

def test_logging_setup():
    """测试日志系统配置"""
    print("=" * 50)
    print("测试1: 日志系统配置")
    print("=" * 50)
    
    try:
        app = Flask(__name__)
        setup_logging(app)
        
        # 测试不同级别的日志
        app.logger.info("这是一条INFO级别的日志")
        app.logger.warning("这是一条WARNING级别的日志")
        app.logger.error("这是一条ERROR级别的日志")
        
        print("✅ 日志系统配置成功")
        print(f"✅ 日志文件位置: {os.path.abspath('logs/app.log')}")
        
        # 检查日志文件是否存在
        if os.path.exists('logs/app.log'):
            print("✅ 日志文件已创建")
            with open('logs/app.log', 'r') as f:
                lines = f.readlines()
                print(f"✅ 日志文件包含 {len(lines)} 行记录")
        else:
            print("❌ 日志文件未创建")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 日志系统配置失败: {str(e)}")
        return False

def test_error_handlers():
    """测试全局错误处理器"""
    print("\n" + "=" * 50)
    print("测试2: 全局错误处理器")
    print("=" * 50)
    
    try:
        from app import app
        
        # 检查错误处理器是否注册
        error_handlers = app.error_handler_spec.get(None, {})
        
        if Exception in error_handlers:
            print("✅ Exception错误处理器已注册")
        else:
            print("❌ Exception错误处理器未注册")
            return False
        
        if 404 in error_handlers:
            print("✅ 404错误处理器已注册")
        else:
            print("❌ 404错误处理器未注册")
            return False
        
        if 500 in error_handlers:
            print("✅ 500错误处理器已注册")
        else:
            print("❌ 500错误处理器未注册")
            return False
        
        print("✅ 所有错误处理器已正确注册")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理器测试失败: {str(e)}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 50)
    print("测试3: 文件结构检查")
    print("=" * 50)
    
    required_files = [
        'config/logging.py',
        '../PoliticsSolver/utils/error-handler.js',
        '../PoliticsSolver/utils/ERROR_HANDLER_USAGE.md',
        'ERROR_HANDLING_IMPLEMENTATION.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("错误处理和用户体验优化 - 实施验证")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(("日志系统配置", test_logging_setup()))
    results.append(("全局错误处理器", test_error_handlers()))
    results.append(("文件结构检查", test_file_structure()))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print("\n" + "=" * 50)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 50)
    
    if passed == total:
        print("\n🎉 所有测试通过！任务11实施成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查实施")
        return 1

if __name__ == '__main__':
    sys.exit(main())
