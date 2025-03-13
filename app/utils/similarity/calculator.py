import pandas as pd
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TextSimilarityCalculator:
    @staticmethod
    def chinese_word_cut(text):
        """中文分词函数"""
        if pd.isnull(text) or not isinstance(text, str):
            return ""
        return " ".join(jieba.cut(text))

    @classmethod
    def calculate_similarity(cls, search_text, results, columns):
        """
        计算文本相似度并排序结果
        
        Args:
            search_text (str): 搜索文本
            results (list): 结果列表
            columns (list): 要搜索的列名列表
            
        Returns:
            list: 按相似度排序的结果列表
        """
        try:
            # 将结果转换为DataFrame，并处理 NaN 值
            df = pd.DataFrame(results)
            
            # 将所有 NaN 值替换为空字符串
            df = df.fillna('')
            
            # 创建合并文本列
            df['合并文本'] = ''
            for column in columns:
                if column in df.columns:
                    # 不需要再次 fillna，因为已经在上面处理过了
                    df['合并文本'] += df[column].astype(str) + ' '
            
            # 应用分词
            df['搜索列分词_cut'] = df['合并文本'].apply(cls.chinese_word_cut)
            
            # 初始化TF-IDF向量器
            vectorizer = TfidfVectorizer()
            
            # 计算TF-IDF矩阵
            tfidf_matrix = vectorizer.fit_transform(df['搜索列分词_cut'])
            
            # 对目标文本进行分词并计算TF-IDF向量
            target_cut = cls.chinese_word_cut(search_text)
            target_tfidf = vectorizer.transform([target_cut])
            
            # 计算余弦相似度
            similarities = cosine_similarity(target_tfidf, tfidf_matrix).flatten()
            
            # 添加相似度列，格式化为百分比字符串
            df['相似度'] = [f"{x:.2f}%" for x in (similarities * 100)]
            
            # 为了保持正确的排序，添加一个数值列
            df['相似度_排序'] = similarities * 100
            
            # 根据数据源选择对应的时间列
            time_column = None
            if '申请时间' in df.columns:  # 快响信息
                time_column = '申请时间'
            elif '发布时间' in df.columns:  # 工程文件
                time_column = '发布时间'
            elif '日期' in df.columns:  # 故障报告
                time_column = '日期'

            # 按相似度降序排序，如果有时间列则按时间升序二次排序
            if time_column:
                # 确保时间列为datetime类型
                df[time_column] = pd.to_datetime(df[time_column], errors='coerce')
                df_sorted = df.sort_values(by=['相似度_排序', time_column], ascending=[False, True])
                # 统一时间格式为 YYYY-MM-DD
                df_sorted[time_column] = df_sorted[time_column].dt.strftime('%Y-%m-%d')
            else:
                # 如果没有时间列，只按相似度排序
                df_sorted = df.sort_values(by='相似度_排序', ascending=False)
            
            # 转换回字典列表时处理 NaN 值
            result_dicts = df_sorted.drop(columns=['合并文本', '搜索列分词_cut', '相似度_排序']).replace({pd.NA: None, float('nan'): None}).to_dict('records')
            return result_dicts
            
        except Exception as e:
            raise Exception(f"计算相似度时出错: {str(e)}") 