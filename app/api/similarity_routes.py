from flask import request, jsonify
from app.api import bp
import logging
from app.utils.similarity import TextSimilarityCalculator

logger = logging.getLogger(__name__)

@bp.route('/similarity', methods=['POST'])
def calculate_text_similarity():
    try:
        data = request.get_json()
        if not data:
            logger.error("相似度计算请求数据为空")
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            }), 400

        # 验证必需的字段
        required_fields = ['text', 'columns', 'results']
        for field in required_fields:
            if field not in data:
                logger.error(f"相似度计算请求缺少必需的字段: {field}")
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必需的字段: {field}'
                }), 400

        # 记录请求信息
        logger.info(f"相似度计算请求: 搜索文本长度={len(data['text'])}, 搜索列={data['columns']}, 结果数量={len(data['results'])}")
        
        # 使用TextSimilarityCalculator计算相似度
        logger.info("开始调用TextSimilarityCalculator.calculate_similarity")
        sorted_results = TextSimilarityCalculator.calculate_similarity(
            data['text'],
            data['results'],
            data['columns']
        )
        logger.info(f"相似度计算完成，结果数量: {len(sorted_results)}")
        
        # 添加序号列
        for index, item in enumerate(sorted_results, 1):
            item['序号'] = index
        
        # 检查结果中是否包含相似度列
        if sorted_results and '相似度' in sorted_results[0]:
            logger.info(f"结果包含相似度列，第一条结果相似度: {sorted_results[0]['相似度']}")
        else:
            logger.warning("结果中不包含相似度列")

        return jsonify({
            'status': 'success',
            'data': sorted_results
        })

    except Exception as e:
        logger.error(f"计算相似度时出错: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'计算相似度失败: {str(e)}'
        }), 500

@bp.route('/similarity_search', methods=['POST'])
def similarity_search():
    """相似度搜索功能"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            }), 400

        # 验证必需的字段
        data_source = data.get('data_source', 'case')
        content = data.get('content', '').strip()
        columns = data.get('columns', [])
        data_types = data.get('data_types', [])
        aircraft_types = data.get('aircraft_types', [])
        
        logger.info(f"相似度搜索请求: 数据源={data_source}, 搜索列={columns}, 数据类型={data_types}, 机型={aircraft_types}")
        logger.info(f"搜索内容长度: {len(content)}")
        
        # 验证搜索内容
        if not content:
            return jsonify({
                'status': 'error',
                'message': '请输入要搜索的内容'
            }), 400
            
        # 验证搜索列
        if not columns or len(columns) == 0:
            return jsonify({
                'status': 'error',
                'message': '请选择要搜索的列'
            }), 400

        # 加载选定的数据源
        df = current_app.load_data_source(data_source)
        if df is None:
            logger.error(f"找不到数据源文件: {current_app.config['DATA_SOURCES'][data_source]}")
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {current_app.config["DATA_SOURCES"][data_source]}'
            }), 404

        logger.info(f"成功加载数据源: {data_source}, 数据行数: {len(df)}")

        # 复制数据框以避免修改原始数据
        result_df = df.copy()
        
        # 首先按数据类型筛选
        if data_types:
            result_df = result_df[result_df['数据类型'].isin(data_types)]
            logger.info(f"按数据类型筛选后的行数: {len(result_df)}")
            
        # 添加机型筛选
        if aircraft_types:
            result_df = result_df[result_df['机型'].isin(aircraft_types)]
            logger.info(f"按机型筛选后的行数: {len(result_df)}")
        
        # 如果没有数据，直接返回空结果
        if result_df.empty:
            logger.info("筛选后没有数据，返回空结果")
            return jsonify({
                'status': 'success',
                'data': [],
                'total': 0
            })
        
        # 将结果转换为字典列表
        results = result_df.to_dict('records')
        logger.info(f"转换为字典列表，数量: {len(results)}")
        
        # 使用TextSimilarityCalculator计算相似度
        logger.info(f"开始计算相似度，搜索列: {columns}")
        sorted_results = TextSimilarityCalculator.calculate_similarity(
            content,
            results,
            columns
        )
        logger.info(f"相似度计算完成，结果数量: {len(sorted_results)}")
        
        # 添加序号列
        for index, item in enumerate(sorted_results, 1):
            item['序号'] = index
        
        return jsonify({
            'status': 'success',
            'data': sorted_results,
            'total': len(sorted_results)
        })

    except Exception as e:
        logger.error(f"相似度搜索时出错: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'相似度搜索失败: {str(e)}'
        }), 500
