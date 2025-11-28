# 数据库设计文档

## 1. 概述

本文档详细描述了小程序后端系统的数据库设计，包括表结构、字段说明、关系约束和设计原则。该数据库用于支持用户管理、题目管理、学习进度跟踪、考试记录等核心功能。

## 2. 技术选型

- 数据库系统：MySQL
- 字符集：utf8mb4
- 排序规则：utf8mb4_unicode_ci
- ORM框架：SQLAlchemy 2.0.43
- 连接库：PyMySQL 1.1.2

## 3. 数据库表结构

### 3.1 用户表 (user)

存储小程序用户的基本信息。

```sql
CREATE TABLE IF NOT EXISTS user (
  id BIGINT NOT NULL AUTO_INCREMENT,
  openid VARCHAR(64) NOT NULL UNIQUE,
  nickname VARCHAR(64),
  avatar_url VARCHAR(256),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_openid (openid)
);
```

**字段说明：**

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT | 用户唯一标识 |
| openid | VARCHAR(64) | UNIQUE, NOT NULL | 微信用户唯一标识 |
| nickname | VARCHAR(64) | - | 用户昵称 |
| avatar_url | VARCHAR(265) | - | 用户头像URL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 用户创建时间 |
| last_login | DATETIME | DEFAULT CURRENT_TIMESTAMP | 最后登录时间 |

### 3.2 题目表 (topic)

存储所有考试题目信息。

```sql
CREATE TABLE IF NOT EXISTS topic (
  id INT NOT NULL AUTO_INCREMENT,
  content TEXT NOT NULL,
  type_id INT NOT NULL COMMENT '1-单选，2-多选，3-判断',
  options TEXT COMMENT 'JSON格式存储选项',
  answer VARCHAR(16) NOT NULL,
  analysis TEXT,
  category_id INT,
  region VARCHAR(32),
  month INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_type (type_id),
  INDEX idx_region (region),
  INDEX idx_month (month)
);
```

**字段说明：**

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 题目唯一标识 |
| content | TEXT | NOT NULL | 题目内容 |
| type_id | INT | NOT NULL | 题目类型（1-单选，2-多选，3-判断） |
| options | TEXT | - | 题目选项（JSON格式） |
| answer | VARCHAR(16) | NOT NULL | 正确答案 |
| analysis | TEXT | - | 题目解析 |
| category_id | INT | - | 分类ID |
| region | VARCHAR(32) | - | 地区 |
| month | INT | - | 月份 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 3.3 用户错题表 (user_mistake)

记录用户做错的题目。

```sql
CREATE TABLE IF NOT EXISTS user_mistake (
  id INT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  topic_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_topic (user_id, topic_id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (topic_id) REFERENCES topic(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id),
  INDEX idx_topic_id (topic_id)
);
```

**字段说明：**

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 错题记录唯一标识 |
| user_id | BIGINT | NOT NULL | 用户ID（外键关联user表） |
| topic_id | INT | NOT NULL | 题目ID（外键关联topic表） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 错题记录创建时间 |

### 3.4 用户收藏表 (user_favorite)

记录用户收藏的题目。

```sql
CREATE TABLE IF NOT EXISTS user_favorite (
  id INT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  topic_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_topic (user_id, topic_id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (topic_id) REFERENCES topic(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id),
  INDEX idx_topic_id (topic_id)
);
```

**字段说明：**

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 收藏记录唯一标识 |
| user_id | BIGINT | NOT NULL | 用户ID（外键关联user表） |
| topic_id | INT | NOT NULL | 题目ID（外键关联topic表） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 收藏记录创建时间 |

### 3.5 考试记录表 (exam_record)

保存用户考试历史。

```sql
CREATE TABLE IF NOT EXISTS exam_record (
  id INT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  score INT NOT NULL,
  total_questions INT NOT NULL,
  correct_count INT NOT NULL,
  wrong_count INT NOT NULL,
  used_time INT NOT NULL COMMENT '秒数',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id),
  INDEX idx_created_at (created_at)
);
```

**字段说明：**

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 考试记录唯一标识 |
| user_id | BIGINT | NOT NULL | 用户ID（外键关联user表） |
| score | INT | NOT NULL | 考试得分 |
| total_questions | INT | NOT NULL | 总题目数 |
| correct_count | INT | NOT NULL | 正确题目数 |
| wrong_count | INT | NOT NULL | 错误题目数 |
| used_time | INT | NOT NULL | 考试用时（秒） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 考试记录创建时间 |

### 3.6 用户题目完成进度表 (user_topic_progress)

跟踪用户每道题的完成情况。通过查询此表可以统计用户每月完成的题目数量。

```sql
CREATE TABLE IF NOT EXISTS user_topic_progress (
  id INT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  topic_id INT NOT NULL,
  month INT NOT NULL,
  completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_topic_month (user_id, topic_id, month),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (topic_id) REFERENCES topic(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id),
  INDEX idx_topic_id (topic_id),
  INDEX idx_month (month)
);
```

**字段说明：**

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 完成记录唯一标识 |
| user_id | BIGINT | NOT NULL | 用户ID（外键关联user表） |
| topic_id | INT | NOT NULL | 题目ID（外键关联topic表） |
| month | INT | NOT NULL | 月份 |
| completed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 完成时间 |

## 4. 表关系图

```
erDiagram
    user ||--o{ user_mistake : has
    user ||--o{ user_favorite : has
    user ||--o{ exam_record : has
    user ||--o{ user_topic_progress : has
    topic ||--o{ user_mistake : contains
    topic ||--o{ user_favorite : contains
    topic ||--o{ user_topic_progress : contains
    
    user {
        BIGINT id PK
        VARCHAR(64) openid UK
        VARCHAR(64) nickname
        VARCHAR(256) avatar_url
        DATETIME created_at
        DATETIME last_login
    }
    
    topic {
        INT id PK
        TEXT content
        INT type_id
        TEXT options
        VARCHAR(16) answer
        TEXT analysis
        INT category_id
        VARCHAR(32) region
        INT month
        DATETIME created_at
    }
    
    user_mistake {
        INT id PK
        BIGINT user_id FK
        INT topic_id FK
        DATETIME created_at
    }
    
    user_favorite {
        INT id PK
        BIGINT user_id FK
        INT topic_id FK
        DATETIME created_at
    }
    
    exam_record {
        INT id PK
        BIGINT user_id FK
        INT score
        INT total_questions
        INT correct_count
        INT wrong_count
        INT used_time
        DATETIME created_at
    }
    
    user_topic_progress {
        INT id PK
        BIGINT user_id FK
        INT topic_id FK
        INT month
        DATETIME completed_at
    }
```

## 5. 设计原则

### 5.1 数据一致性
- 所有涉及用户和题目的表都通过外键约束关联到主表
- 使用 `ON DELETE CASCADE` 确保当用户或题目被删除时，相关记录自动清理

### 5.2 性能优化
- 为常用查询字段添加索引
- 将明细数据和汇总数据分离存储，提高查询效率
- 使用适当的数据类型以节省存储空间

### 5.3 可扩展性
- 使用 BIGINT 类型存储用户ID，支持大规模用户场景
- 采用模块化表设计，便于功能扩展

### 5.4 安全性
- 用户敏感信息（如openid）进行唯一性约束
- 通过外键约束保证数据引用完整性

## 6. 使用说明

### 6.1 初始化
数据库通过 [init.sql](file:///Users/decay/Desktop/backend/mysql/init.sql) 脚本初始化，该脚本会创建所有必要的表和索引。

### 6.2 数据访问
应用通过 SQLAlchemy ORM 访问数据库，相关模型定义在 [app.py](file:///Users/decay/Desktop/backend/app.py) 中。

### 6.3 数据维护
- 定期备份重要数据
- 监控数据库性能，根据需要调整索引
- 注意用户数据的隐私保护