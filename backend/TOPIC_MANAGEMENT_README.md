# 题目数据管理文档

本文档介绍如何使用题目数据管理工具进行PDF题目提取、数据验证、批量导入和备份。

## 目录

- [功能概述](#功能概述)
- [环境配置](#环境配置)
- [PDF题目提取](#pdf题目提取)
- [批量导入API](#批量导入api)
- [数据备份](#数据备份)
- [测试工具](#测试工具)
- [常见问题](#常见问题)

## 功能概述

题目数据管理系统提供以下功能：

1. **PDF题目提取**: 从PDF文件中自动提取题目、选项、答案和解析
2. **数据验证**: 验证题目数据的完整性和有效性
3. **数据清洗**: 自动清理和格式化题目数据
4. **批量导入**: 支持批量导入题目到数据库
5. **重复检测**: 自动检测并跳过重复题目
6. **数据备份**: 支持JSON和SQL格式的数据备份
7. **管理API**: 提供RESTful API进行题目管理

## 环境配置

### 1. 安装依赖

确保已安装所有必需的Python包：

```bash
cd backend
pip install -r requirements.txt
```

额外需要安装PDF处理库：

```bash
pip install PyMuPDF  # fitz库
```

### 2. 配置环境变量

在 `backend/.env` 文件中配置数据库连接：

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=sz_exam

# 管理员密钥（用于API认证）
ADMIN_KEY=your_secure_admin_key
```

### 3. 配置PDF文件路径

编辑 `backend/questions/extractPDF.py`，配置要处理的PDF文件：

```python
PDF_FILES = [
    os.path.join(SCRIPT_DIR, "24年7-12月时政汇总.pdf"),
    os.path.join(SCRIPT_DIR, "最新时政汇总（更新至4.7），有答案！！.pdf"),
    # 添加更多PDF文件...
]
```

## PDF题目提取

### 基本用法

```bash
cd backend/questions

# 提取并导入所有配置的PDF文件
python extractPDF.py --extract

# 提取并导入单个PDF文件
python extractPDF.py --pdf "path/to/your/file.pdf"

# 仅备份数据库（不提取）
python extractPDF.py --backup
```

### 数据验证规则

提取的题目数据会自动进行以下验证：

1. **必需字段检查**: content, options, answer, month, type_id
2. **题目内容**: 长度至少5个字符
3. **选项检查**: 必须有4个选项（A、B、C、D）
4. **答案检查**: 不能为空或'X'，必须是有效的选项字母
5. **月份检查**: 必须在1-12之间
6. **题型检查**: type_id必须是1（单选）、2（多选）或3（判断）

### 数据清洗

系统会自动清洗数据：

- 去除多余空格
- 统一答案格式为大写
- 确保月份为整数类型
- 清理选项内容中的换行符

### 日志记录

提取过程会生成日志文件 `pdf_extraction.log`，包含：

- 提取进度信息
- 验证失败的题目
- 数据库操作结果
- 错误和警告信息

## 批量导入API

### 1. 批量导入题目

**接口**: `POST /api/admin/topics/import`

**请求头**:
```
Content-Type: application/json
X-Admin-Key: your_admin_key
```

**请求体**:
```json
{
  "topics": [
    {
      "content": "题目内容",
      "type_id": 1,
      "options": [
        {"key": "A", "content": "选项A"},
        {"key": "B", "content": "选项B"},
        {"key": "C", "content": "选项C"},
        {"key": "D", "content": "选项D"}
      ],
      "answer": "A",
      "analysis": "解析内容（可选）",
      "month": 5,
      "region": "北京（可选）",
      "category_id": 1
    }
  ]
}
```

**响应**:
```json
{
  "code": 0,
  "message": "导入完成",
  "data": {
    "inserted": 100,
    "skipped": 5,
    "errors": []
  }
}
```

### 2. 获取题目统计

**接口**: `GET /api/admin/topics/statistics`

**请求头**:
```
X-Admin-Key: your_admin_key
```

**响应**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "totalCount": 1500,
    "byType": {
      "1": 800,
      "2": 500,
      "3": 200
    },
    "byMonth": {
      "1": 120,
      "2": 130,
      "3": 125
    },
    "byRegion": {
      "北京": 300,
      "上海": 250
    }
  }
}
```

### 3. 备份题目数据

**接口**: `GET /api/admin/topics/backup`

**请求头**:
```
X-Admin-Key: your_admin_key
```

**响应**:
```json
{
  "code": 0,
  "message": "备份成功",
  "data": {
    "filename": "topics_backup_20241120_153000.json",
    "total": 1500,
    "topics": [...]
  }
}
```

## 数据备份

### 使用备份脚本

```bash
cd backend/scripts

# 备份为JSON格式（默认）
python backup_topics.py

# 备份为SQL格式
python backup_topics.py --format sql

# 指定输出目录
python backup_topics.py --output /path/to/backup/dir

# 完整示例
python backup_topics.py --format json --output ../backups
```

### 备份文件格式

**JSON格式** (`topics_backup_YYYYMMDD_HHMMSS.json`):
```json
{
  "backup_time": "2024-11-20 15:30:00",
  "total_count": 1500,
  "topics": [
    {
      "id": 1,
      "content": "题目内容",
      "type_id": 1,
      "options": [...],
      "answer": "A",
      "month": 5,
      ...
    }
  ]
}
```

**SQL格式** (`topics_backup_YYYYMMDD_HHMMSS.sql`):
```sql
-- 题目数据备份
-- 备份时间: 2024-11-20 15:30:00
-- 题目数量: 1500

USE sz_exam;

INSERT INTO topic (...) VALUES (...);
...
```

### 定期备份

建议设置定时任务进行定期备份：

```bash
# 添加到crontab
# 每天凌晨2点备份
0 2 * * * cd /path/to/backend/scripts && python backup_topics.py
```

## 测试工具

### 测试PDF提取

```bash
cd backend/scripts

# 测试默认PDF文件
python test_import.py

# 测试指定PDF文件
python test_import.py --pdf ../questions/your_file.pdf

# 仅测试提取，不导入数据库
python test_import.py --dry-run

# 测试数据验证功能
python test_import.py --test-validation
```

### 测试输出示例

```
============================================================
测试PDF提取: ../questions/24年7-12月时政汇总.pdf
============================================================

正在提取PDF数据...

提取结果:
  总题目数: 150

按月份统计:
  7月: 25 题
  8月: 25 题
  9月: 25 题
  10月: 25 题
  11月: 25 题
  12月: 25 题

按题型统计:
  单选题: 100 题
  多选题: 40 题
  判断题: 10 题

数据验证:
  有效题目: 148
  无效题目: 2

题目示例 (前3题):
  题目 1:
    月份: 7
    类型: 单选题
    题干: 2024年7月1日，习近平总书记在庆祝中国共产党成立...
    答案: A
    验证: ✓ 通过
```

## 常见问题

### 1. PDF提取失败

**问题**: 无法提取PDF中的题目

**解决方案**:
- 检查PDF文件是否损坏
- 确认PDF格式符合预期（包含月份标题、题号、选项等）
- 查看 `pdf_extraction.log` 日志文件获取详细错误信息
- 调整正则表达式匹配规则

### 2. 数据验证失败

**问题**: 大量题目验证失败

**解决方案**:
- 检查PDF格式是否标准
- 确认答案是否正确提取（不是'X'）
- 查看日志中的具体验证错误信息
- 手动检查几个失败的题目

### 3. 重复题目

**问题**: 导入时提示大量重复题目

**解决方案**:
- 系统会自动跳过重复题目（基于content和month）
- 如需重新导入，先清空相关数据
- 检查是否多次运行了导入脚本

### 4. 数据库连接失败

**问题**: 无法连接到数据库

**解决方案**:
- 检查 `.env` 文件中的数据库配置
- 确认MySQL服务正在运行
- 验证数据库用户权限
- 检查防火墙设置

### 5. 内存不足

**问题**: 处理大型PDF时内存不足

**解决方案**:
- 分批处理PDF文件
- 使用 `--pdf` 参数单独处理每个文件
- 调整批量插入大小（batch_size参数）

## 最佳实践

1. **定期备份**: 在导入新数据前先备份现有数据
2. **测试先行**: 使用 `--dry-run` 模式先测试提取效果
3. **日志监控**: 定期检查日志文件，及时发现问题
4. **数据验证**: 导入后使用统计API验证数据完整性
5. **版本控制**: 保留PDF源文件，便于追溯和重新导入

## 技术支持

如遇到问题，请：

1. 查看日志文件 `pdf_extraction.log`
2. 运行测试工具诊断问题
3. 检查数据库连接和权限
4. 联系技术支持团队

---

最后更新: 2024-11-20
