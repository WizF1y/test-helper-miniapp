#!/usr/bin/env python3
"""
验证题目数据管理功能实现

此脚本验证以下功能:
1. PDF提取脚本的数据验证功能
2. 数据清洗功能
3. 备份功能的基本结构
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from questions.extractPDF import validate_topic_data, clean_topic_data


def test_validation():
    """测试数据验证功能"""
    print("=" * 60)
    print("测试数据验证功能")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {
            'name': '✓ 有效的单选题',
            'data': {
                'content': '这是一道测试题目，内容足够长',
                'type_id': 1,
                'options': [
                    {'key': 'A', 'content': '选项A'},
                    {'key': 'B', 'content': '选项B'},
                    {'key': 'C', 'content': '选项C'},
                    {'key': 'D', 'content': '选项D'}
                ],
                'answer': 'A',
                'month': 5
            },
            'expected': True
        },
        {
            'name': '✗ 缺少答案',
            'data': {
                'content': '这是一道测试题目',
                'type_id': 1,
                'options': [
                    {'key': 'A', 'content': '选项A'},
                    {'key': 'B', 'content': '选项B'},
                    {'key': 'C', 'content': '选项C'},
                    {'key': 'D', 'content': '选项D'}
                ],
                'answer': 'X',
                'month': 5
            },
            'expected': False
        },
        {
            'name': '✗ 选项不足4个',
            'data': {
                'content': '这是一道测试题目',
                'type_id': 1,
                'options': [
                    {'key': 'A', 'content': '选项A'},
                    {'key': 'B', 'content': '选项B'}
                ],
                'answer': 'A',
                'month': 5
            },
            'expected': False
        },
        {
            'name': '✗ 题目内容过短',
            'data': {
                'content': '短',
                'type_id': 1,
                'options': [
                    {'key': 'A', 'content': '选项A'},
                    {'key': 'B', 'content': '选项B'},
                    {'key': 'C', 'content': '选项C'},
                    {'key': 'D', 'content': '选项D'}
                ],
                'answer': 'A',
                'month': 5
            },
            'expected': False
        },
        {
            'name': '✗ 月份无效',
            'data': {
                'content': '这是一道测试题目',
                'type_id': 1,
                'options': [
                    {'key': 'A', 'content': '选项A'},
                    {'key': 'B', 'content': '选项B'},
                    {'key': 'C', 'content': '选项C'},
                    {'key': 'D', 'content': '选项D'}
                ],
                'answer': 'A',
                'month': 13
            },
            'expected': False
        },
        {
            'name': '✓ 有效的多选题',
            'data': {
                'content': '这是一道多选题测试题目',
                'type_id': 2,
                'options': [
                    {'key': 'A', 'content': '选项A'},
                    {'key': 'B', 'content': '选项B'},
                    {'key': 'C', 'content': '选项C'},
                    {'key': 'D', 'content': '选项D'}
                ],
                'answer': 'ABC',
                'month': 5
            },
            'expected': True
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        is_valid, error_msg = validate_topic_data(test_case['data'])
        expected = test_case['expected']
        
        status = "✓" if is_valid == expected else "✗"
        result = "通过" if is_valid == expected else "失败"
        
        print(f"\n{status} {test_case['name']}: {result}")
        
        if is_valid != expected:
            print(f"  预期: {'有效' if expected else '无效'}")
            print(f"  实际: {'有效' if is_valid else '无效'}")
            if error_msg:
                print(f"  错误: {error_msg}")
            failed += 1
        else:
            passed += 1
            if not is_valid and error_msg:
                print(f"  错误信息: {error_msg}")
    
    print(f"\n{'='*60}")
    print(f"验证测试结果: {passed} 通过, {failed} 失败")
    print(f"{'='*60}\n")
    
    return failed == 0


def test_cleaning():
    """测试数据清洗功能"""
    print("=" * 60)
    print("测试数据清洗功能")
    print("=" * 60)
    
    # 测试数据（包含多余空格和格式问题）
    dirty_data = {
        'content': '  这是一道   测试题目  \n  包含多余空格  ',
        'type_id': 1,
        'options': [
            {'key': 'A', 'content': '  选项A  \n  '},
            {'key': 'B', 'content': '选项B   '},
            {'key': 'C', 'content': '  选项C'},
            {'key': 'D', 'content': '选项D'}
        ],
        'answer': '  a  ',  # 小写且有空格
        'month': '5',  # 字符串类型
        'analysis': '  这是解析   内容  '
    }
    
    print("\n原始数据:")
    print(f"  题目: '{dirty_data['content']}'")
    print(f"  答案: '{dirty_data['answer']}'")
    print(f"  月份: {dirty_data['month']} (类型: {type(dirty_data['month']).__name__})")
    print(f"  选项A: '{dirty_data['options'][0]['content']}'")
    
    # 清洗数据
    cleaned_data = clean_topic_data(dirty_data)
    
    print("\n清洗后数据:")
    print(f"  题目: '{cleaned_data['content']}'")
    print(f"  答案: '{cleaned_data['answer']}'")
    print(f"  月份: {cleaned_data['month']} (类型: {type(cleaned_data['month']).__name__})")
    print(f"  选项A: '{cleaned_data['options'][0]['content']}'")
    
    # 验证清洗结果
    checks = [
        ('题目无多余空格', '  ' not in cleaned_data['content']),
        ('答案已转大写', cleaned_data['answer'] == 'A'),
        ('月份为整数', isinstance(cleaned_data['month'], int)),
        ('选项无多余空格', '  ' not in cleaned_data['options'][0]['content'])
    ]
    
    print("\n清洗验证:")
    all_passed = True
    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        result = "通过" if check_result else "失败"
        print(f"  {status} {check_name}: {result}")
        if not check_result:
            all_passed = False
    
    print(f"\n{'='*60}")
    print(f"清洗测试结果: {'全部通过' if all_passed else '存在失败'}")
    print(f"{'='*60}\n")
    
    return all_passed


def test_api_structure():
    """测试API接口结构"""
    print("=" * 60)
    print("测试API接口结构")
    print("=" * 60)
    
    # 检查app.py中是否包含新增的API接口
    app_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
    
    with open(app_file, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    required_apis = [
        ('/api/admin/topics/import', '批量导入题目'),
        ('/api/admin/topics/backup', '备份题目数据'),
        ('/api/admin/topics/statistics', '获取题目统计')
    ]
    
    print("\n检查API接口:")
    all_found = True
    for api_path, api_desc in required_apis:
        found = api_path in app_content
        status = "✓" if found else "✗"
        result = "已实现" if found else "未找到"
        print(f"  {status} {api_path} ({api_desc}): {result}")
        if not found:
            all_found = False
    
    print(f"\n{'='*60}")
    print(f"API接口检查: {'全部实现' if all_found else '存在缺失'}")
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
        ('verify_implementation.py', '验证脚本')
    ]
    
    print("\n检查脚本文件:")
    all_exist = True
    for script_name, script_desc in required_scripts:
        script_path = os.path.join(scripts_dir, script_name)
        exists = os.path.exists(script_path)
        status = "✓" if exists else "✗"
        result = "存在" if exists else "缺失"
        print(f"  {status} {script_name} ({script_desc}): {result}")
        if not exists:
            all_exist = False
    
    # 检查文档
    doc_path = os.path.join(os.path.dirname(scripts_dir), 'TOPIC_MANAGEMENT_README.md')
    doc_exists = os.path.exists(doc_path)
    status = "✓" if doc_exists else "✗"
    result = "存在" if doc_exists else "缺失"
    print(f"  {status} TOPIC_MANAGEMENT_README.md (管理文档): {result}")
    if not doc_exists:
        all_exist = False
    
    print(f"\n{'='*60}")
    print(f"文件检查: {'全部存在' if all_exist else '存在缺失'}")
    print(f"{'='*60}\n")
    
    return all_exist


def main():
    print("\n" + "="*60)
    print("题目数据管理功能验证")
    print("="*60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(('数据验证功能', test_validation()))
    results.append(('数据清洗功能', test_cleaning()))
    results.append(('API接口结构', test_api_structure()))
    results.append(('脚本文件检查', test_scripts_exist()))
    
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
        print("\n✓ 所有验证通过！题目数据管理功能已正确实现。\n")
        return 0
    else:
        print("\n✗ 部分验证失败，请检查上述错误信息。\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
