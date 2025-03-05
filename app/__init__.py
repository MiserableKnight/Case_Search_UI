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

# 加载环境变量
load_dotenv()

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 数据源配置
DATA_SOURCES = {
    'case': 'case.parquet',
    'engineering': 'engineering.parquet',
    'manual': 'manual.parquet'
}

# 数据缓存
data_frames = {}

def load_data_source(source):
    """加载指定数据源的数据"""
    if source not in data_frames:
        try:
            data_path = os.path.join(os.path.dirname(__file__), "data", DATA_SOURCES[source])
            if os.path.exists(data_path):
                print(f"加载数据源 {source} 从: {data_path}")
                data_frames[source] = pd.read_parquet(data_path)
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
        # 检查列是否存在
        if column_name not in df.columns:
            raise ValueError(f"列 '{column_name}' 不存在于当前数据源中")
        columns_to_search = [column_name]
    elif isinstance(column_name, list):
        # 过滤掉不存在的列
        columns_to_search = [col for col in column_name if col in df.columns]
        if not columns_to_search:
            raise ValueError("所选列在当前数据源中均不存在")
    else:
        raise TypeError("column_name格式不正确")
    
    # 创建一个空的布尔序列，用于存储最终的过滤结果
    if logic == 'and':
        final_mask = pd.Series(True, index=df.index)
        for keyword in keywords:
            keyword_mask = pd.Series(False, index=df.index)
            for col in columns_to_search:
                # 确保列值为字符串并进行小写转换
                col_values = df[col].fillna('').astype(str).str.lower()
                keyword_mask |= col_values.str.contains(keyword, na=False, regex=False)
            final_mask &= keyword_mask
    else:  # logic == 'or'
        final_mask = pd.Series(False, index=df.index)
        for keyword in keywords:
            for col in columns_to_search:
                # 确保列值为字符串并进行小写转换
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
        data_source = data.get('data_source', 'case')  # 获取数据源
        search_levels = data.get('search_levels', [])
        data_types = data.get('data_types', [])
        
        # 加载选定的数据源
        df = load_data_source(data_source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {DATA_SOURCES[data_source]}'
            }), 404

        # 添加调试信息
        print(f"搜索使用的数据源: {data_source}")
        print(f"数据源的列: {df.columns.tolist()}")
        print(f"搜索条件: {search_levels}")
        
        # 复制数据框以避免修改原始数据
        result_df = df.copy()
        
        # 首先按数据类型筛选
        if data_types:
            result_df = result_df[result_df['数据类型'].isin(data_types)]
        
        # 处理每个搜索层级
        for level in search_levels:
            keywords = level.get('keywords', '').strip()
            column_name = level.get('column_name')
            logic = level.get('logic', 'and')
            negative = level.get('negative_filtering', False)
            
            if not keywords:
                continue
                
            try:
                # 处理搜索
                result_df = search_column(result_df, keywords, column_name, logic, negative)
            except ValueError as e:
                # 返回具体的错误信息
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        # 转换结果为列表
        results = result_df.to_dict('records')
        
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
        columns = data.get('columns', ['问题描述'])  # 获取要搜索的列
        results = data.get('results', [])  # 获取当前搜索结果
        
        if not text.strip():
            return jsonify({
                'status': 'error',
                'message': '搜索文本不能为空'
            }), 400
            
        # 将当前搜索结果转换为DataFrame
        df = pd.DataFrame(results)
        
        # 计算相似度
        result_df = calculate_similarity(df, text, columns)
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
    """计算文本相似度并按相似度和时间排序
    
    参数:
    - df: 包含文本的DataFrame
    - query_text: 目标文本
    - columns: 要搜索的列名列表
    """
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
        
        # 确定时间列名
        time_column = '发布时间' if '发布时间' in df.columns else '申请时间'
        
        # 确保时间列为datetime类型并格式化
        df[time_column] = pd.to_datetime(df[time_column], errors='coerce')
        df[time_column] = df[time_column].dt.strftime('%Y-%m-%d')
        
        # 排序：首先按相似度降序，其次按时间升序
        result_df = df.sort_values(
            by=['相似度', time_column], 
            ascending=[False, True]
        )
        
        # 将相似度转换为百分比格式
        result_df['相似度'] = result_df['相似度'].apply(lambda x: f"{x*100:.2f}%")
        
        # 选择需要显示的列，排除临时列
        columns_to_keep = [col for col in result_df.columns if col != '搜索列分词_cut']
        
        return result_df[columns_to_keep]
        
    except Exception as e:
        print(f"计算相似度时出错: {str(e)}")
        raise e 