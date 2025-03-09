import json
import re

# 加载敏感词列表
def load_sensitive_words(file_path):
    sensitive_words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            sensitive_words = json.loads(content)

            unique_sensitive_words = []
            for word in sensitive_words:
                if word not in unique_sensitive_words:
                    unique_sensitive_words.append(word)
            sensitive_words = unique_sensitive_words
            print("敏感词列表读取成功")
    except FileNotFoundError:
        print("未找到 '脱敏.txt' 文件，请检查文件路径和文件名。")
    except Exception as e:
        print(f"读取文件时出现错误：{e}")
    return sensitive_words

# 初始加载敏感词
file_path = r'D:\Quant\working\数据存储与转换\脱敏.txt'
current_sensitive_words = load_sensitive_words(file_path)

# 初始正则模式
current_patterns = [
    r'(909|ARJ)/B-?[A-Z0-9]{4}',
    r'B-?[A-Z0-9]{4}',
    r'10\d{3}',
    r'执行.{1,15}?航班',
    r'[A-Z]{2}\d{4}'
]

# 添加新敏感词的函数
def add_sensitive_words(new_words):
    if isinstance(new_words, str):
        new_words = [new_words]
    for word in new_words:
        if word not in current_sensitive_words:
            current_sensitive_words.append(word)

# 添加新正则模式的函数
def add_patterns(new_patterns):
    if isinstance(new_patterns, str):
        new_patterns = [new_patterns]
    for pattern in new_patterns:
        if pattern not in current_patterns:
            current_patterns.append(pattern)
            
# 对初始敏感词列表按长度降序排序
current_sensitive_words.sort(key=len, reverse=True)

# 定义脱敏函数
def anonymize_text(text):
    if isinstance(text, str):
        for pattern in current_patterns:
            text = re.sub(pattern, "", text)
        for word in current_sensitive_words:
            text = text.replace(word, "")
        return text
    return text

# 获取当前敏感词列表的函数
def get_sensitive_words():
    return current_sensitive_words

# 获取当前正则表达式模式列表的函数
def get_patterns():
    return current_patterns