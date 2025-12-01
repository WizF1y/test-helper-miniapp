-- 创建数据库
CREATE DATABASE IF NOT EXISTS sz_exam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sz_exam;

-- 用户表
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

-- 题目表
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

-- 用户错题表
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

-- 用户收藏表
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

-- 考试记录表
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

-- 考试详情表
CREATE TABLE IF NOT EXISTS exam_detail (
  id INT NOT NULL AUTO_INCREMENT,
  exam_record_id INT NOT NULL,
  topic_id INT NOT NULL,
  user_answer VARCHAR(16),
  is_correct BOOLEAN,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (exam_record_id) REFERENCES exam_record(id) ON DELETE CASCADE,
  FOREIGN KEY (topic_id) REFERENCES topic(id) ON DELETE CASCADE,
  INDEX idx_exam_record (exam_record_id),
  INDEX idx_topic_id (topic_id)
);

-- 用户题目完成进度表
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

-- 支付记录表
CREATE TABLE IF NOT EXISTS payment (
  id INT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  order_no VARCHAR(64) NOT NULL UNIQUE,
  amount INT NOT NULL COMMENT '单位：分',
  status INT NOT NULL DEFAULT 0 COMMENT '0-待支付, 1-已支付, 2-已退款',
  transaction_id VARCHAR(64),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  paid_at DATETIME,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id),
  INDEX idx_order_no (order_no),
  INDEX idx_status (status)
);