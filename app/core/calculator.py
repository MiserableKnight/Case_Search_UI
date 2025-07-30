import logging
from typing import Any, Dict, List

import jieba
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
logger = logging.getLogger(__name__)


class TextSimilarityCalculator:
    @staticmethod
    def chinese_word_cut(text: str) -> str:
        """中文分词函数"""
        if pd.isnull(text) or not isinstance(text, str):
            return ""
        return " ".join(jieba.cut(text))

    @classmethod
    def calculate_similarity(
        cls, search_text: str, results: List[Dict[str, Any]], columns: List[str]
    ) -> List[Dict[str, Any]]:
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
            # 验证输入参数
            if not search_text or not isinstance(search_text, str):
                raise ValueError("搜索文本不能为空且必须是字符串类型")

            if not results:
                logger.info("结果列表为空，返回空列表")
                return []

            if not columns or not isinstance(columns, list):
                raise ValueError("必须指定至少一个搜索列且必须是列表类型")

            logger.info(
                f"开始计算相似度，搜索文本长度: {len(search_text)}, 结果数量: {len(results)}, 搜索列: {columns}"
            )

            # 将结果转换为DataFrame，并处理 NaN 值
            df = pd.DataFrame(results)
            if df.empty:
                logger.info("转换后的DataFrame为空，返回空列表")
                return []

            logger.info(f"DataFrame创建成功，列名: {df.columns.tolist()}")

            # 验证所有指定的列都存在
            missing_columns = [col for col in columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"以下列在数据中不存在: {', '.join(missing_columns)}")

            # 将所有 NaN 值替换为空字符串
            df = df.fillna("")

            # 创建合并文本列
            df["合并文本"] = ""
            for column in columns:
                df["合并文本"] += df[column].astype(str) + " "

            logger.info(
                f"合并文本列创建成功，样本: {df['合并文本'].iloc[0][:100] if not df.empty else '无数据'}"
            )

            # 应用分词
            df["搜索列分词_cut"] = df["合并文本"].apply(cls.chinese_word_cut)

            logger.info(
                f"分词完成，样本: {df['搜索列分词_cut'].iloc[0][:100] if not df.empty else '无数据'}"
            )

            # 初始化TF-IDF向量器
            vectorizer = TfidfVectorizer()

            try:
                # 计算TF-IDF矩阵
                tfidf_matrix = vectorizer.fit_transform(df["搜索列分词_cut"])
                logger.info(f"TF-IDF矩阵计算完成，形状: {tfidf_matrix.shape}")

                # 对目标文本进行分词并计算TF-IDF向量
                target_cut = cls.chinese_word_cut(search_text)
                target_tfidf = vectorizer.transform([target_cut])
                logger.info(f"目标文本TF-IDF向量计算完成，形状: {target_tfidf.shape}")

                # 计算余弦相似度
                similarities = cosine_similarity(target_tfidf, tfidf_matrix).flatten()
            except Exception as e:
                logger.error(f"TF-IDF计算过程出错: {str(e)}", exc_info=True)
                raise ValueError(f"相似度计算失败: {str(e)}")

            logger.info(
                f"余弦相似度计算完成，最大值: {similarities.max() if len(similarities) > 0 else '无数据'}, 最小值: {similarities.min() if len(similarities) > 0 else '无数据'}"
            )

            # 添加相似度列，格式化为百分比字符串
            df["相似度"] = [f"{x:.2f}%" for x in (similarities * 100)]

            # 为了保持正确的排序，添加一个数值列
            df["相似度_排序"] = similarities * 100

            # 根据数据源选择对应的时间列
            time_column = None
            if "申请时间" in df.columns:  # 快响信息
                time_column = "申请时间"
            elif "发布时间" in df.columns:  # 工程文件
                time_column = "发布时间"
            elif "日期" in df.columns:  # 故障报告
                time_column = "日期"

            logger.info(f"选择的时间列: {time_column}")

            try:
                # 按相似度降序排序，如果有时间列则按时间升序二次排序
                if time_column:
                    # 确保时间列为datetime类型
                    df[time_column] = pd.to_datetime(df[time_column], errors="coerce")
                    df_sorted = df.sort_values(
                        by=["相似度_排序", time_column], ascending=[False, True]
                    )
                    # 统一时间格式为 YYYY-MM-DD
                    df_sorted[time_column] = df_sorted[time_column].dt.strftime(
                        "%Y-%m-%d"
                    )
                else:
                    # 如果没有时间列，只按相似度排序
                    df_sorted = df.sort_values(by="相似度_排序", ascending=False)

                logger.info(f"排序完成，结果数量: {len(df_sorted)}")
            except Exception as e:
                logger.error(f"排序过程出错: {str(e)}", exc_info=True)
                # 如果排序失败，使用未排序的数据框
                df_sorted = df
                logger.warning("排序失败，使用未排序的结果")

            # 转换回字典列表时处理 NaN 值
            try:
                result_dicts = (
                    df_sorted.drop(
                        columns=["合并文本", "搜索列分词_cut", "相似度_排序"]
                    )
                    .replace({pd.NA: None, float("nan"): None})
                    .to_dict("records")
                )
                logger.info(f"转换为字典列表完成，结果数量: {len(result_dicts)}")
                return result_dicts
            except Exception as e:
                logger.error(f"转换为字典列表时出错: {str(e)}", exc_info=True)
                raise ValueError(f"结果转换失败: {str(e)}")

        except Exception as e:
            logger.error(f"计算相似度时出错: {str(e)}", exc_info=True)
            raise ValueError(f"计算相似度时出错: {str(e)}")
