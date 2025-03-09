from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from functools import reduce
import operator
import time
import os
from dotenv import load_dotenv
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import re
import json
from app.utils.word_manager import SensitiveWordManager

# 加载环境变量
load_dotenv()

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 数据源配置
DATA_SOURCES = {
    'case': 'case.parquet',
    'engineering': 'engineering.parquet',
    'manual': 'manual.parquet',
    'faults': 'faults.parquet'  # 添加故障报告数据源
}

# 数据缓存
data_frames = {}

word_manager = SensitiveWordManager()

def load_data_source(source):
    """加载指定数据源的数据"""
    if source not in data_frames:
        try:
            data_path = os.path.join(os.path.dirname(__file__), "data", DATA_SOURCES[source])
            if os.path.exists(data_path):
                print(f"加载数据源 {source} 从: {data_path}")
                data_frames[source] = pd.read_parquet(data_path)
                
                # 添加机型检查
                if '机型' in data_frames[source].columns:
                    unique_types = data_frames[source]['机型'].unique()
                    print(f"数据源 {source} 中的所有机型类别: {unique_types.tolist()}")
                    
                    # 检查是否存在未知机型
                    valid_types = {'ARJ21', 'C919', '无', None, '', np.nan}
                    unknown_types = set(unique_types) - valid_types
                    if unknown_types:
                        print(f"警告：发现未知机型: {unknown_types}")
                        raise ValueError(f"数据源 {source} 中存在未知机型: {unknown_types}")
                
                print(f"数据源 {source} 加载成功，形状: {data_frames[source].shape}")
            else:
                print(f"数据文件不存在: {data_path}")
                return None
        except Exception as e:
            print(f"加载数据源 {source} 时出错: {str(e)}")
            return None
    return data_frames[source]

def search_column(df, keywords, column_name, logic='and', negative_filtering=False):
    """基础搜索功能"""
    if not keywords:
        return df
        
    # 将所有关键字转换为小写
    if isinstance(keywords, str):
        keywords = keywords.replace('，', ',')
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    keywords = [str(k).lower() for k in keywords]
    
    # 确定要搜索的列
    if column_name == 'all' or column_name == ['all']:
        columns_to_search = df.columns.tolist()
    elif isinstance(column_name, str):
        columns_to_search = [column_name]
    elif isinstance(column_name, list):
        columns_to_search = [col for col in column_name if col in df.columns]
    
    # 使用相同的搜索逻辑
    if logic == 'and':
        final_mask = pd.Series(True, index=df.index)
        for keyword in keywords:
            keyword_mask = pd.Series(False, index=df.index)
            for col in columns_to_search:
                col_values = df[col].fillna('').astype(str).str.lower()
                keyword_mask |= col_values.str.contains(keyword, na=False, regex=False)
            final_mask &= keyword_mask
    else:  # logic == 'or'
        final_mask = pd.Series(False, index=df.index)
        for keyword in keywords:
            for col in columns_to_search:
                col_values = df[col].fillna('').astype(str).str.lower()
                final_mask |= col_values.str.contains(keyword, na=False, regex=False)
    
    # 根据negative_filtering参数决定是否反向过滤
    return df[~final_mask] if negative_filtering else df[final_mask]

@app.route('/api/data_source_columns', methods=['GET'])
def get_data_source_columns():
    """获取所有数据源的列名"""
    try:
        columns = {}
        for source in DATA_SOURCES:
            df = load_data_source(source)
            if df is not None:
                # 这里我们过滤掉了一些列
                columns[source] = df.columns.tolist()
            else:
                columns[source] = []
        
        return jsonify({
            'status': 'success',
            'columns': columns
        })
    except Exception as e:
        print(f"获取数据源列名时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/data_types/<source>', methods=['GET'])
def get_data_types(source):
    """获取指定数据源的数据类型"""
    try:
        if source not in DATA_SOURCES:
            return jsonify({
                'status': 'error',
                'message': '无效的数据源'
            }), 400
        
        df = load_data_source(source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {DATA_SOURCES[source]}'
            }), 404
        
        # 添加调试信息
        print(f"数据源 {source} 的列名: {df.columns.tolist()}")
        
        if '数据类型' not in df.columns:
            print(f"警告：数据源 {source} 中没有找到'数据类型'列")
            return jsonify({
                'status': 'error',
                'message': f"数据源 {source} 中没有'数据类型'列"
            }), 500
        
        # 添加调试信息
        print(f"数据源 {source} 的数据类型: {df['数据类型'].unique().tolist()}")
        
        data_types = sorted(df['数据类型'].unique().tolist())
        
        return jsonify({
            'status': 'success',
            'types': data_types
        })
    except Exception as e:
        print(f"获取数据类型时出错: {str(e)}")  # 添加错误详情打印
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """搜索数据"""
    try:
        data = request.get_json()
        data_source = data.get('data_source', 'case')  # 获取数据源，默认为'case'
        search_levels = data.get('search_levels', [])
        data_types = data.get('data_types', [])
        aircraft_types = data.get('aircraft_types', [])
        
        # 加载选定的数据源
        df = load_data_source(data_source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {DATA_SOURCES[data_source]}'
            }), 404

        # 复制数据框以避免修改原始数据
        result_df = df.copy()
        
        # 首先按数据类型筛选
        if data_types:
            result_df = result_df[result_df['数据类型'].isin(data_types)]
            
        # 添加机型筛选
        if aircraft_types:
            result_df = result_df[result_df['机型'].isin(aircraft_types)]
        
        # 处理每个搜索层级，使用相同的search_column函数
        for level in search_levels:
            keywords = level.get('keywords', '').strip()
            column_name = level.get('column_name')
            logic = level.get('logic', 'and')
            negative = level.get('negative_filtering', False)
            
            if not keywords:
                continue
                
            try:
                result_df = search_column(result_df, keywords, column_name, logic, negative)
            except ValueError as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        # 在返回结果之前，格式化C919的飞机序列号
        results = result_df.to_dict('records')
        if data_source == 'faults':
            for item in results:
                if item.get('机型') == 'C919' and '飞机序列号' in item:
                    item['飞机序列号'] = format_msn(item['飞机序列号'])
        
        return jsonify({
            'status': 'success',
            'data': results,
            'total': len(results)
        })
            
    except Exception as e:
        print(f"搜索时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/similarity', methods=['POST'])
def similarity_search():
    """仅在用户请求相似度搜索时执行"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        columns = data.get('columns', ['问题描述'])
        results = data.get('results', [])
        
        if not text.strip():
            return jsonify({
                'status': 'error',
                'message': '搜索文本不能为空'
            }), 400
            
        # 将当前搜索结果转换为DataFrame
        df = pd.DataFrame(results)
        
        # 计算相似度
        result_df = calculate_similarity(df, text, columns)
        
        # 确保相似度列在第一位
        if '相似度' in result_df.columns:
            cols = result_df.columns.tolist()
            cols.remove('相似度')
            result_df = result_df[['相似度'] + cols]
        
        results = result_df.to_dict('records')
        
        return jsonify({
            'status': 'success',
            'data': results,
            'total': len(results)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """仅在用户请求AI分析时执行"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        results = data.get('results', [])
        
        if not query.strip() or not results:
            return jsonify({
                'status': 'error',
                'message': '分析请求参数不完整'
            }), 400
            
        # 这里可以添加实际的AI分析逻辑
        import requests
        
        # 构建提示词
        prompt = f"请分析以下案例并回答问题：\n\n案例数据：{str(results)}\n\n问题：{query}"
        
        # 调用API
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        
        if response.status_code == 200:
            summary = response.json()['choices'][0]['message']['content']
        else:
            summary = "AI分析请求失败，请稍后重试。"
            
        return jsonify({
            'status': 'success',
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def calculate_similarity(df, query_text, columns):
    """计算文本相似度并按相似度和时间排序"""
    try:
        # 确保所有列都存在
        valid_columns = [col for col in columns if col in df.columns]
        if not valid_columns:
            raise ValueError("没有找到可用于计算相似度的列")
            
        # 定义分词函数
        def chinese_word_cut(text):
            if pd.isnull(text) or not isinstance(text, str):
                return ""
            return " ".join(jieba.cut(text))
            
        # 合并选定列的文本
        df['搜索列分词_cut'] = df[valid_columns].fillna('').astype(str).apply(
            lambda x: chinese_word_cut(' '.join(x)), axis=1
        )
        
        # 初始化TF-IDF向量器
        vectorizer = TfidfVectorizer()
        
        # 计算TF-IDF矩阵
        tfidf_matrix = vectorizer.fit_transform(df['搜索列分词_cut'])
        
        # 对目标文本进行分词并计算TF-IDF向量
        target_cut = chinese_word_cut(query_text)
        target_tfidf = vectorizer.transform([target_cut])
        
        # 计算余弦相似度
        similarities = cosine_similarity(target_tfidf, tfidf_matrix).flatten()
        
        # 添加相似度列
        df['相似度'] = similarities
        
        # 更新时间列名判断逻辑
        time_column = None
        if '发布时间' in df.columns:
            time_column = '发布时间'
        elif '申请时间' in df.columns:
            time_column = '申请时间'
        elif '日期' in df.columns:
            time_column = '日期'
            
        if time_column:
            # 确保时间列为datetime类型并格式化
            df[time_column] = pd.to_datetime(df[time_column], errors='coerce')
            df[time_column] = df[time_column].dt.strftime('%Y-%m-%d')
            
            # 排序：首先按相似度降序，其次按时间升序
            result_df = df.sort_values(
                by=['相似度', time_column], 
                ascending=[False, True]
            )
        else:
            # 如果没有时间列，只按相似度排序
            result_df = df.sort_values('相似度', ascending=False)
        
        # 将相似度转换为百分比格式
        result_df['相似度'] = result_df['相似度'].apply(lambda x: f"{x*100:.2f}%")
        
        # 选择需要显示的列，排除临时列
        columns_to_keep = [col for col in result_df.columns if col != '搜索列分词_cut']
        
        return result_df[columns_to_keep]
        
    except Exception as e:
        print(f"计算相似度时出错: {str(e)}")
        raise e

@app.route('/api/anonymize', methods=['POST'])
def anonymize_results():
    """对搜索结果进行脱敏处理"""
    try:
        data = request.get_json()
        results = data.get('results', [])
        data_source = data.get('dataSource', 'case')
        
        # 根据数据源确定需要脱敏的字段
        if data_source == 'engineering':
            fields = ["原因和说明", "原文文本", "文件名称"]
        elif data_source == 'faults':
            fields = ["问题描述", "排故措施"]  # 故障报告只脱敏这两列
        else:
            fields = ["问题描述", "答复详情"]
        
        # 直接获取已排序的敏感词列表
        sensitive_words = word_manager.get_sorted_words()
        
        print(f"准备进行脱敏的敏感词数量: {len(sensitive_words)}")  # 调试信息
        
        # 转换为DataFrame进行处理
        df = pd.DataFrame(results)
        
        # 对指定列进行脱敏
        for col in fields:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: anonymize_text(x, sensitive_words))
        
        return jsonify({
            'status': 'success',
            'data': df.to_dict('records')
        })
    except Exception as e:
        print(f"脱敏处理出错: {str(e)}")  # 添加错误日志
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def anonymize_text(text, sensitive_words):
    """文本脱敏处理"""
    if not isinstance(text, str):
        return text
    
    # 替换特定模式
    patterns = [
        # 删除这两个可能与敏感词冲突的模式
        # r'\s*ARJ21\s*',
        # r'\bCF34-10A\b',
        r'(909|ARJ)/B-?[A-Z0-9]{4}',# 修改为更精确的注册号格式
        r'B-?33[A-Z0-9]{2}',
        r'B-?10[A-Z0-9]{2}',
        r'B-?60[A-Z0-9]{2}',
        r'B-?62[A-Z0-9]{2}',
        r'B-?65[A-Z0-9]{2}',
        r'B-?91[A-Z0-9]{2}',
        # r'10\d{3}',
        r'执行.{1,15}?航班',
        r'[A-Z]{2}\d{4}'
    ]
    
    # 先处理敏感词列表
    for word in sensitive_words:
        if word and word.strip():  # 确保敏感词不为空
            text = text.replace(word, "")
    
    # 然后处理正则表达式模式
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    
    return text

@app.route('/api/sensitive_words', methods=['GET'])
def get_sensitive_words():
    try:
        words = word_manager.get_all_words()
        return jsonify({
            'status': 'success',
            'words': words
        })
    except Exception as e:
        print(f"获取敏感词失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensitive_words', methods=['POST'])
def add_sensitive_word():
    try:
        data = request.get_json()
        word = data.get('word')
        category = data.get('category')
        
        if not word or not category:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        success, message = word_manager.add_word(word, category)
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
    except Exception as e:
        print(f"添加敏感词失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensitive_words', methods=['DELETE'])
def delete_sensitive_word():
    try:
        data = request.get_json()
        word = data.get('word')
        category = data.get('category')
        
        if not word or not category:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        success, message = word_manager.remove_word(word, category)
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
    except Exception as e:
        print(f"删除敏感词失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def format_msn(value):
    """格式化C919的机身序列号为5位数字"""
    try:
        if pd.isna(value) or not str(value).strip():
            return value
        
        # 如果是纯数字，进行格式化
        if str(value).isdigit():
            return f"{int(value):05d}"
        return value
    except:
        return value