from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from functools import reduce
import operator
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 Flask 应用
app = Flask(__name__)

# 配置
API_KEY = os.getenv("DEEPSEEK_API_KEY", "4a21773226c140289b8c1b897d9c8e98")
API_URL = "https://wishub-x1.ctyun.cn/v1/chat/completions"

# 加载数据
def load_data():
    try:
        print("开始加载数据...")
        data_path = os.path.join(os.path.dirname(__file__), "data", "search_data.parquet")
        print(f"数据文件路径: {os.path.abspath(data_path)}")
        print(f"文件是否存在: {os.path.exists(data_path)}")
        
        start_time = time.time()
        df = pd.read_parquet(data_path)
        end_time = time.time()
        
        print(f"数据加载完成，耗时: {end_time - start_time:.2f} 秒")
        print(f"数据形状: {df.shape}")
        print(f"数据列名: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"数据加载错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return pd.DataFrame()

# 初始化数据
print("初始化应用...")
search_data = load_data()
print("应用初始化完成")

def search_column(df, keywords, column_name, logic='and', negative_filtering=0):
    """基础搜索功能 - 使用向量化操作进行高效搜索"""
    if not keywords:
        return df
        
    # 将所有关键字转换为小写，并确保是字符串列表
    if isinstance(keywords, str):
        # 替换中文逗号为英文逗号，然后分割
        keywords = keywords.replace('，', ',')
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    keywords = [str(k).lower() for k in keywords]
    
    # 确定要搜索的列
    if column_name == ['all']:
        columns_to_search = df.columns.tolist()
    elif isinstance(column_name, str):
        columns_to_search = [column_name]
    elif isinstance(column_name, list):
        columns_to_search = column_name
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
    elif logic == 'or':
        final_mask = pd.Series(False, index=df.index)
        for keyword in keywords:
            for col in columns_to_search:
                # 确保列值为字符串并进行小写转换
                col_values = df[col].fillna('').astype(str).str.lower()
                final_mask |= col_values.str.contains(keyword, na=False, regex=False)
    else:
        raise ValueError("logic 参数必须是 'and' 或 'or'")
    
    # 根据negative_filtering参数决定是否反向过滤
    return df[~final_mask] if negative_filtering else df[final_mask]

def calculate_similarity(df, target_text, columns=None):
    """相似度搜索功能 - 使用jieba分词和TF-IDF计算余弦相似度"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import jieba
        
        def chinese_word_cut(text):
            if pd.isnull(text) or not isinstance(text, str):
                return ""
            return " ".join(jieba.cut(text))
            
        df = df.copy()
        
        # 如果没有指定列，默认使用'问题描述'
        if not columns:
            columns = ['问题描述']
            
        # 计算每列的相似度
        max_similarities = []
        for column in columns:
            if column not in df.columns:
                continue
                
            # 对所有文本进行分词
            corpus = df[column].fillna('').apply(chinese_word_cut)
            target_cut = chinese_word_cut(target_text)
            
            # 使用TF-IDF向量化
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([target_cut] + list(corpus))
            
            # 计算余弦相似度
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # 更新最大相似度
            if len(max_similarities) == 0:
                max_similarities = similarities
            else:
                max_similarities = np.maximum(max_similarities, similarities)
        
        # 添加相似度列（保留原始数值用于排序）
        df['相似度_raw'] = max_similarities
        df['相似度'] = df['相似度_raw'].apply(lambda x: f"{x*100:.2f}%")
        
        # 添加相似度整数部分列用于分组排序
        df['相似度_整数'] = df['相似度_raw'].apply(lambda x: int(x*100))
        
        # 创建临时时间列用于排序，保持原始时间列不变
        df['申请时间_排序'] = pd.to_datetime(df['申请时间'], errors='coerce')
        
        # 先按相似度整数降序，相同的再按申请时间降序
        df_sorted = df.sort_values(
            by=['相似度_整数', '申请时间_排序'], 
            ascending=[False, False]
        )
        
        # 删除临时列
        df_sorted = df_sorted.drop(['相似度_raw', '相似度_整数', '申请时间_排序'], axis=1)
        
        return df_sorted
    except Exception as e:
        print(f"相似度计算错误: {str(e)}")
        return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/columns')
def get_columns():
    try:
        columns = search_data.columns.tolist()
        return jsonify({
            'status': 'success',
            'columns': columns
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        search_levels = data.get('search_levels', [])
        
        if not search_levels:
            return jsonify({
                'status': 'error',
                'message': '搜索参数不能为空'
            }), 400
        
        # 初始结果为完整数据集
        result_df = search_data.copy()  # 创建副本以避免修改原始数据
        
        print("开始漏斗式搜索...")  # 添加调试日志
        print(f"初始数据集大小: {len(result_df)}")  # 添加调试日志
        
        # 依次应用每个搜索条件，每次在上一次的结果上继续搜索
        for i, level in enumerate(search_levels, 1):
            keywords = level.get('keywords', '')
            if not keywords:  # 跳过空的搜索条件
                continue
                
            column_name = level.get('column_name', ['all'])
            logic = level.get('logic', 'and')
            negative_filtering = level.get('negative_filtering', False)
            
            # 在当前结果集上应用搜索条件
            current_result = search_column(result_df, keywords, column_name, logic, negative_filtering)
            print(f"第{i}重搜索条件: {keywords}")  # 添加调试日志
            print(f"搜索列: {column_name}")  # 添加调试日志
            print(f"逻辑: {logic}")  # 添加调试日志
            print(f"反向过滤: {negative_filtering}")  # 添加调试日志
            print(f"当前结果数量: {len(current_result)}")  # 添加调试日志
            
            # 更新结果集为当前搜索结果
            result_df = current_result
            
            # 如果没有结果了，就提前退出
            if len(result_df) == 0:
                print("搜索结果为空，提前退出")  # 添加调试日志
                break
        
        results = result_df.to_dict('records')
        
        print(f"最终搜索结果数量: {len(results)}")  # 添加调试日志
        
        return jsonify({
            'status': 'success',
            'data': results,
            'total': len(results)
        })
    except Exception as e:
        print(f"搜索错误: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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