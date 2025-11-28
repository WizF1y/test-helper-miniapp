import fitz  # PyMuPDF
import re
from mysql import connector
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- !!! USER CONFIGURATION REQUIRED !!! ---
# 1. 数据库连接设置（从环境变量读取）
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'sz_exam')
}

# 2. 设置数据库写入的格式
TABLE_NAME = 'topic' # 表名
COLUMN_CONTENT = 'content' # 题干列名
COLUMN_TYPEINT = 'type_id' # 题目类型列名
COLUMN_MONTH = 'month' # 月份列名
COLUMN_OPTIONS = 'options' # 选项列名
COLUMN_ANSWER = ''
COLUMN_ANALYSIS = ''
COLUMN_CATEGORY = ''
COLUMN_REGION = ''


# 3. 待写入的pdf文件
# 获取脚本所在目录，确保路径正确
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_FILES = [
    os.path.join(SCRIPT_DIR, "24年7-12月时政汇总.pdf"),
    os.path.join(SCRIPT_DIR, "最新时政汇总（更新至4.7），有答案！！.pdf"),
    os.path.join(SCRIPT_DIR, "最新时政汇总（更新至4.18），有答案！！.pdf")
]
# --- !!! 用户配置结束 !!! ---

def validate_topic_data(topic_data):
    """
    验证题目数据的完整性和有效性
    
    Args:
        topic_data: 题目数据字典
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # 必需字段检查
    required_fields = ['content', 'options', 'answer', 'month', 'type_id']
    for field in required_fields:
        if field not in topic_data or topic_data[field] is None:
            return False, f"缺少必需字段: {field}"
    
    # 题目内容检查
    content = topic_data['content'].strip()
    if len(content) < 5:
        return False, "题目内容过短"
    
    # 选项检查
    options = topic_data['options']
    if not isinstance(options, list) or len(options) != 4:
        return False, "选项必须为4个"
    
    for opt in options:
        if not isinstance(opt, dict) or 'key' not in opt or 'content' not in opt:
            return False, "选项格式错误"
        if opt['key'] not in ['A', 'B', 'C', 'D']:
            return False, f"选项键值错误: {opt['key']}"
        if not opt['content'].strip():
            return False, f"选项{opt['key']}内容为空"
    
    # 答案检查
    answer = topic_data['answer'].strip()
    if not answer or answer == 'X':
        return False, "答案缺失"
    
    # 验证答案是否在有效范围内
    valid_answer_chars = set('ABCD')
    if not all(c in valid_answer_chars for c in answer):
        return False, f"答案包含无效字符: {answer}"
    
    # 月份检查
    month = topic_data['month']
    if not isinstance(month, (int, str)) or int(month) < 1 or int(month) > 12:
        return False, f"月份值无效: {month}"
    
    # 题型检查
    type_id = topic_data['type_id']
    if type_id not in [1, 2, 3]:
        return False, f"题型ID无效: {type_id}"
    
    return True, None


def clean_topic_data(topic_data):
    """
    清洗题目数据
    
    Args:
        topic_data: 题目数据字典
        
    Returns:
        dict: 清洗后的题目数据
    """
    cleaned = topic_data.copy()
    
    # 清理题目内容
    cleaned['content'] = ' '.join(cleaned['content'].split())
    
    # 清理选项内容
    for opt in cleaned['options']:
        opt['content'] = ' '.join(opt['content'].split())
    
    # 确保答案大写
    cleaned['answer'] = cleaned['answer'].upper().strip()
    
    # 确保月份为整数
    cleaned['month'] = int(cleaned['month'])
    
    # 如果有解析字段，也进行清理
    if 'analysis' in cleaned and cleaned['analysis']:
        cleaned['analysis'] = ' '.join(cleaned['analysis'].split())
    
    return cleaned


def extract_data_from_pdf(pdf_path):
    """
    Extracts questions, options, and month context from a single PDF.
    """
    extracted_data = []
    current_month = None
    question_buffer = {} # Temporarily store parts of a question

    try:
        doc = fitz.open(pdf_path)
        logger.info(f"Processing PDF: {pdf_path} ({doc.page_count} pages)")

        # Regex patterns
        # Pattern to find month headers (e.g., "2025年3月时事政治题库")
        month_pattern = re.compile(r"\d{4}年(\d{1,2})月时事政治题库")
        # Pattern to find start of a question (e.g., "1.", "52.")
        question_start_pattern = re.compile(r"^\s*(\d+)\.\s*(.*)", re.MULTILINE)
        # Pattern to find options (e.g., "A.", "B.") - allows multi-line options somewhat
        option_pattern = re.compile(r"^\s*([ABCD])\.\s*(.*)", re.MULTILINE)
        # Pattern to identify page footers/headers to ignore (adjust if needed)
        ignore_pattern = re.compile(r"师达教育|师有道|华南教师考编|咨询:|微信同号|回复时政|获取最新|周更新一次", re.IGNORECASE)
        # Pattern to right answer
        answer_pattern = re.compile(r"【正确答案】([A-D]+)")
        # Pattern to specifically detect end of options/start of next question more reliably
        next_question_or_end_pattern = re.compile(r"^\s*\d+\.\s*") # Looks for the next question number

        full_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            # Extract text blocks to better handle structure
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: b[1]) # Sort blocks top-to-bottom

            for block in blocks:
                block_text = block[4].strip() # The text content of the block
                # print(block_text)
                # Skip ignored blocks (headers/footers)
                if ignore_pattern.search(block_text) or block_text.isdigit(): # Skip page numbers too
                     continue
                # Check for month update first
                # print(block_text)
                month_match = month_pattern.search(block_text)
                if month_match:
                    current_month = month_match.group(1)
                    logger.info(f"  Found month section: {current_month}")
                    # If we find a new month, clear any incomplete question buffer
                    question_buffer = {}
                    continue # Move to next block after finding month

                # If no month context yet, skip blocks until we find one
                if not current_month:
                    continue

                # Process lines within the block
                lines = block_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    q_match = question_start_pattern.match(line)
                    opt_match = option_pattern.match(line)
                    answer_match = answer_pattern.search(line)

                    if q_match:
                        # print(q_match)
                        # Found a new question, process the previous one if exists
                        if question_buffer and 'num' in question_buffer and len(question_buffer.get('options', {})) == 4:
                            # 获取题干内容
                            question_content = question_buffer.get('text', '').strip()
                            # 判断是否为多选题
                            type_id = 2 if '多选' in question_content else 1
                            
                            # 构建选项数组
                            options = [
                                {"key": "A", "content": question_buffer.get('options', {}).get('A', '').strip()},
                                {"key": "B", "content": question_buffer.get('options', {}).get('B', '').strip()},
                                {"key": "C", "content": question_buffer.get('options', {}).get('C', '').strip()},
                                {"key": "D", "content": question_buffer.get('options', {}).get('D', '').strip()}
                            ]
                            
                            topic_data = {
                                'month': current_month,
                                'type_id': type_id,
                                'content': question_content,
                                'options': options,
                                'answer': question_buffer.get('answer', 'X')
                            }
                            
                            # 验证和清洗数据
                            is_valid, error_msg = validate_topic_data(topic_data)
                            if is_valid:
                                cleaned_data = clean_topic_data(topic_data)
                                extracted_data.append(cleaned_data)
                            else:
                                logger.warning(f"跳过无效题目 (题号: {question_buffer.get('num')}): {error_msg}")

                        # Start a new question buffer
                        question_buffer = {
                            'num': q_match.group(1),
                            'text': q_match.group(2),
                            'options': {}
                        }
                    elif answer_match and 'num' in question_buffer:
                        # print(answer_match)
                        # 匹配到答案
                        question_buffer['answer'] = answer_match.group(1)
                    elif opt_match and 'num' in question_buffer:
                        # Found an option for the current question
                        option_letter = opt_match.group(1)
                        option_text = opt_match.group(2)
                        question_buffer.setdefault('options', {})[option_letter] = option_text
                        # Clear text buffer for option accumulation if needed in future
                        # question_buffer['current_option_text'] = ''
                    elif 'num' in question_buffer:
                         # This line doesn't start a new question or an option
                         # Append to question text if no options found yet
                         if not question_buffer.get('options'):
                              question_buffer['text'] = question_buffer.get('text','') + ' ' + line
                         # Append to the last found option if options are being collected
                         elif question_buffer.get('options'):
                             last_option = sorted(question_buffer['options'].keys())[-1] if question_buffer['options'] else None
                             if last_option:
                                 # Only append if it doesn't look like the start of the next question
                                 if not next_question_or_end_pattern.match(line):
                                    question_buffer['options'][last_option] += ' ' + line


        # Add the very last question buffered after the loop finishes
        if question_buffer and 'num' in question_buffer and len(question_buffer.get('options', {})) == 4:
            question_content = question_buffer.get('text', '').strip()
            type_id = 2 if '多选' in question_content else 1
            # 构建选项数组
            options = [
                {"key": "A", "content": question_buffer.get('options', {}).get('A', '').strip()},
                {"key": "B", "content": question_buffer.get('options', {}).get('B', '').strip()},
                {"key": "C", "content": question_buffer.get('options', {}).get('C', '').strip()},
                {"key": "D", "content": question_buffer.get('options', {}).get('D', '').strip()}
            ]
            topic_data = {
                'month': current_month,
                'type_id': type_id,
                'content': question_content,
                'options': options,
                'answer': question_buffer.get('answer', 'X')
            }
            
            # 验证和清洗数据
            is_valid, error_msg = validate_topic_data(topic_data)
            if is_valid:
                cleaned_data = clean_topic_data(topic_data)
                extracted_data.append(cleaned_data)
            else:
                logger.warning(f"跳过无效题目 (题号: {question_buffer.get('num')}): {error_msg}")

        doc.close()
        logger.info(f"  Finished processing {pdf_path}. Found {len(extracted_data)} valid questions.")

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")

    return extracted_data


def insert_data_to_mysql(data_list, batch_size=100):
    """
    Inserts the extracted data into the MySQL database.
    
    Args:
        data_list: 题目数据列表
        batch_size: 批量插入的大小
        
    Returns:
        dict: 插入结果统计
    """
    if not data_list:
        logger.warning("No data to insert.")
        return {'inserted': 0, 'skipped': 0, 'duplicates': 0}

    conn = None
    cursor = None
    inserted_count = 0
    skipped_count = 0
    duplicate_count = 0

    # 检查重复的SQL
    check_duplicate_sql = f"""
        SELECT COUNT(*) FROM {TABLE_NAME}
        WHERE content = %s AND month = %s
    """
    
    # 插入SQL
    insert_sql = f"""
        INSERT INTO {TABLE_NAME} 
        (month, type_id, content, options, answer, analysis, category_id, region)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    logger.info(f"\nConnecting to database '{DB_CONFIG['database']}' on '{DB_CONFIG['host']}'...")
    try:
        conn = connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Database connection successful.")
        logger.info(f"Attempting to insert {len(data_list)} records into table '{TABLE_NAME}'...")

        for i, item in enumerate(data_list):
            # 获取字段值
            month = item.get('month', None)
            type_int = item.get('type_id', None)
            content = item.get('content', '')
            options = json.dumps(item.get('options', []), ensure_ascii=False)
            answer = item.get('answer', 'X')
            
            # 数据库插入
            if month is not None:
                # 检查是否重复
                try:
                    cursor.execute(check_duplicate_sql, (content, month))
                    count = cursor.fetchone()[0]
                    if count > 0:
                        logger.debug(f"  Skipping duplicate record (Month: {month})")
                        duplicate_count += 1
                        continue
                except connector.Error as err:
                    logger.warning(f"  Error checking duplicate: {err}")
                
                data_tuple = (
                    month,          # 对应第一个 %s：月份
                    type_int,       # 对应第二个 %s：题目类型
                    content,        # 对应第三个 %s：题目内容
                    options,        # 对应第四个 %s：选项JSON
                    answer,         # 对应第五个 %s：实际答案
                    None,           # 对应第六个 %s：解析
                    None,           # 对应第七个 %s：分类ID
                    None            # 对应第八个 %s：地区
                )
                try:
                    cursor.execute(insert_sql, data_tuple)
                    inserted_count += 1
                    
                    # 批量提交
                    if (i + 1) % batch_size == 0:
                        conn.commit()
                        logger.info(f"  Committed {i + 1} records...")
                        
                except connector.Error as err:
                    logger.error(f"  Error inserting record (Month: {month}): {err}")
                    skipped_count += 1
            else:
                logger.warning(f"  Skipping record due to missing month: {item}")
                skipped_count += 1

        # 最后提交剩余的记录
        conn.commit()
        logger.info(f"\nInsertion complete.")
        logger.info(f"  Successfully inserted: {inserted_count} records.")
        logger.info(f"  Duplicates skipped: {duplicate_count} records.")
        logger.info(f"  Skipped due to errors: {skipped_count} records.")
        
        return {
            'inserted': inserted_count,
            'duplicates': duplicate_count,
            'skipped': skipped_count
        }

    except connector.Error as err:
        logger.error(f"Database Error: {err}")
        if conn:
            conn.rollback()
        return {
            'inserted': inserted_count,
            'duplicates': duplicate_count,
            'skipped': skipped_count
        }

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            logger.info("Database connection closed.")

def backup_database(backup_dir='backups'):
    """
    备份数据库中的题目数据到JSON文件
    
    Args:
        backup_dir: 备份目录
        
    Returns:
        str: 备份文件路径
    """
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'topics_backup_{timestamp}.json')
    
    conn = None
    cursor = None
    
    try:
        logger.info(f"Starting database backup...")
        conn = connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有题目
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        topics = cursor.fetchall()
        
        # 转换日期时间为字符串
        for topic in topics:
            if 'created_at' in topic and topic['created_at']:
                topic['created_at'] = topic['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 写入JSON文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Backup completed: {backup_file}")
        logger.info(f"Total topics backed up: {len(topics)}")
        
        return backup_file
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# --- Main Execution ---
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF题目提取和数据库管理工具')
    parser.add_argument('--backup', action='store_true', help='备份数据库')
    parser.add_argument('--extract', action='store_true', help='提取PDF并导入数据库')
    parser.add_argument('--pdf', type=str, help='指定单个PDF文件路径')
    
    args = parser.parse_args()
    
    if args.backup:
        # 执行备份
        backup_database()
    elif args.extract or args.pdf:
        # 执行提取和导入
        all_extracted_data = []
        
        if args.pdf:
            # 处理单个PDF文件
            if os.path.exists(args.pdf):
                logger.info(f"Processing single PDF: {args.pdf}")
                extracted = extract_data_from_pdf(args.pdf)
                all_extracted_data.extend(extracted)
            else:
                logger.error(f"PDF file not found: {args.pdf}")
        else:
            # 处理配置的所有PDF文件
            for pdf_file in PDF_FILES:
                if os.path.exists(pdf_file):
                    extracted = extract_data_from_pdf(pdf_file)
                    all_extracted_data.extend(extracted)
                else:
                    logger.warning(f"PDF file not found - {pdf_file}")
        
        if all_extracted_data:
            logger.info(f"\nTotal extracted questions: {len(all_extracted_data)}")
            result = insert_data_to_mysql(all_extracted_data)
            logger.info(f"\nFinal statistics:")
            logger.info(f"  Inserted: {result['inserted']}")
            logger.info(f"  Duplicates: {result['duplicates']}")
            logger.info(f"  Skipped: {result['skipped']}")
        else:
            logger.warning("\nNo data was extracted from the PDF files.")
    else:
        # 默认行为：提取并导入
        logger.info("Starting PDF extraction and import process...")
        all_extracted_data = []
        
        for pdf_file in PDF_FILES:
            if os.path.exists(pdf_file):
                extracted = extract_data_from_pdf(pdf_file)
                all_extracted_data.extend(extracted)
            else:
                logger.warning(f"PDF file not found - {pdf_file}")
        
        if all_extracted_data:
            logger.info(f"\nTotal extracted questions: {len(all_extracted_data)}")
            result = insert_data_to_mysql(all_extracted_data)
            logger.info(f"\nFinal statistics:")
            logger.info(f"  Inserted: {result['inserted']}")
            logger.info(f"  Duplicates: {result['duplicates']}")
            logger.info(f"  Skipped: {result['skipped']}")
        else:
            logger.warning("\nNo data was extracted from the PDF files.")