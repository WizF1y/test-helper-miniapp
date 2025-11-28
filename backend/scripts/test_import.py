#!/usr/bin/env python3
"""
测试PDF题目导入流程

用法:
    python test_import.py                      # 测试默认PDF文件
    python test_import.py --pdf path/to/file   # 测试指定PDF文件
    python test_import.py --dry-run            # 仅测试提取，不导入数据库
"""

import os
import sys
import json
import argparse

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from questions.extractPDF import (
    extract_data_from_pdf,
    validate_topic_data,
    clean_topic_data,
    insert_data_to_mysql
)


def test_extraction(pdf_path):
    """
    测试PDF提取功能
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        list: 提取的题目数据
    """
    print(f"\n{'='*60}")
    print(f"测试PDF提取: {pdf_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(pdf_path):
        print(f"✗ 错误: PDF文件不存在: {pdf_path}")
        return []
    
    # 提取数据
    print("正在提取PDF数据...")
    extracted_data = extract_data_from_pdf(pdf_path)
    
    print(f"\n提取结果:")
    print(f"  总题目数: {len(extracted_data)}")
    
    if not extracted_data:
        print("  ✗ 未提取到任何题目")
        return []
    
    # 统计信息
    by_month = {}
    by_type = {}
    valid_count = 0
    invalid_count = 0
    
    for topic in extracted_data:
        # 月份统计
        month = topic.get('month')
        by_month[month] = by_month.get(month, 0) + 1
        
        # 题型统计
        type_id = topic.get('type_id')
        by_type[type_id] = by_type.get(type_id, 0) + 1
        
        # 验证统计
        is_valid, _ = validate_topic_data(topic)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
    
    print(f"\n按月份统计:")
    for month in sorted(by_month.keys()):
        print(f"  {month}月: {by_month[month]} 题")
    
    print(f"\n按题型统计:")
    type_names = {1: '单选题', 2: '多选题', 3: '判断题'}
    for type_id in sorted(by_type.keys()):
        type_name = type_names.get(type_id, f'未知类型{type_id}')
        print(f"  {type_name}: {by_type[type_id]} 题")
    
    print(f"\n数据验证:")
    print(f"  有效题目: {valid_count}")
    print(f"  无效题目: {invalid_count}")
    
    # 显示前3个题目示例
    print(f"\n题目示例 (前3题):")
    for i, topic in enumerate(extracted_data[:3], 1):
        print(f"\n  题目 {i}:")
        print(f"    月份: {topic.get('month')}")
        print(f"    类型: {type_names.get(topic.get('type_id'), '未知')}")
        print(f"    题干: {topic.get('content', '')[:50]}...")
        print(f"    答案: {topic.get('answer')}")
        
        is_valid, error_msg = validate_topic_data(topic)
        if is_valid:
            print(f"    验证: ✓ 通过")
        else:
            print(f"    验证: ✗ 失败 - {error_msg}")
    
    return extracted_data


def test_validation():
    """
    测试数据验证功能
    """
    print(f"\n{'='*60}")
    print("测试数据验证功能")
    print(f"{'='*60}\n")
    
    # 测试用例
    test_cases = [
        {
            'name': '有效的单选题',
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
                'month': 5
            },
            'expected': True
        },
        {
            'name': '缺少答案',
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
            'name': '选项不足4个',
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
            'name': '月份无效',
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
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        is_valid, error_msg = validate_topic_data(test_case['data'])
        expected = test_case['expected']
        
        if is_valid == expected:
            print(f"✓ {test_case['name']}: 通过")
            passed += 1
        else:
            print(f"✗ {test_case['name']}: 失败")
            print(f"  预期: {'有效' if expected else '无效'}")
            print(f"  实际: {'有效' if is_valid else '无效'}")
            if error_msg:
                print(f"  错误: {error_msg}")
            failed += 1
    
    print(f"\n测试结果: {passed} 通过, {failed} 失败")


def test_import(extracted_data, dry_run=False):
    """
    测试数据导入功能
    
    Args:
        extracted_data: 提取的题目数据
        dry_run: 是否仅测试不实际导入
    """
    print(f"\n{'='*60}")
    print(f"测试数据导入 {'(模拟模式)' if dry_run else ''}")
    print(f"{'='*60}\n")
    
    if not extracted_data:
        print("✗ 没有数据可导入")
        return
    
    if dry_run:
        print(f"模拟导入 {len(extracted_data)} 条题目...")
        print("✓ 模拟导入完成 (未实际写入数据库)")
    else:
        print(f"正在导入 {len(extracted_data)} 条题目到数据库...")
        result = insert_data_to_mysql(extracted_data)
        
        print(f"\n导入结果:")
        print(f"  成功插入: {result['inserted']}")
        print(f"  重复跳过: {result['duplicates']}")
        print(f"  错误跳过: {result['skipped']}")


def main():
    parser = argparse.ArgumentParser(description='测试PDF题目导入流程')
    parser.add_argument('--pdf', help='指定PDF文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅测试提取，不导入数据库')
    parser.add_argument('--test-validation', action='store_true', help='测试数据验证功能')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("PDF题目导入测试工具")
    print("="*60)
    
    # 测试验证功能
    if args.test_validation:
        test_validation()
        return
    
    # 确定PDF文件路径
    if args.pdf:
        pdf_path = args.pdf
    else:
        # 使用默认的测试PDF
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pdf_path = os.path.join(script_dir, 'questions', '24年7-12月时政汇总.pdf')
    
    # 测试提取
    extracted_data = test_extraction(pdf_path)
    
    # 测试导入
    if extracted_data:
        test_import(extracted_data, dry_run=args.dry_run)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
