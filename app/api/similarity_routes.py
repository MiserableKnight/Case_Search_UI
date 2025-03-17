from flask import request
from app.api import bp
import logging
from app.services import SimilarityService
from app.services.api_response import ApiResponse
from app.core.error_handler import BadRequestError, ValidationError, InternalError

logger = logging.getLogger(__name__)

# 创建SimilarityService实例
similarity_service = SimilarityService()

@bp.route('/similarity', methods=['POST'])
def calculate_text_similarity():
    try:
        data = request.get_json()
        if not data:
            logger.error("相似度计算请求数据为空")
            raise BadRequestError('无效的请求数据')

        # 验证必需的字段
        required_fields = ['text', 'columns', 'results']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"相似度计算请求缺少必需的字段: {missing_fields}")
            raise ValidationError(f'缺少必需的字段: {", ".join(missing_fields)}', details={'missing_fields': missing_fields})

        # 记录请求信息
        logger.info(f"相似度计算请求: 搜索文本长度={len(data['text'])}, 搜索列={data['columns']}, 结果数量={len(data['results'])}")
        
        # 使用SimilarityService计算相似度
        logger.info("开始调用SimilarityService.calculate_similarity")
        sorted_results = similarity_service.calculate_batch_similarity(
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
        
        return ApiResponse.success(
            data=sorted_results,
            message="相似度计算成功"
        )
        
    except (BadRequestError, ValidationError) as e:
        # 这些错误会被全局错误处理器捕获
        raise
    except Exception as e:
        logger.error(f"相似度计算过程中发生错误: {str(e)}")
        raise InternalError(f"相似度计算失败: {str(e)}")

@bp.route('/similarity_search', methods=['POST'])
def similarity_search():
    try:
        data = request.get_json()
        if not data:
            raise BadRequestError('无效的请求数据')
        
        # 验证必需的字段
        required_fields = ['text', 'dataSource', 'columns', 'limit']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f'缺少必需的字段: {", ".join(missing_fields)}', details={'missing_fields': missing_fields})
        
        # 获取参数
        search_text = data['text']
        data_source = data['dataSource']
        columns = data['columns']
        limit = int(data['limit'])
        
        # 记录请求信息
        logger.info(f"相似度搜索请求: 数据源={data_source}, 搜索文本长度={len(search_text)}, 搜索列={columns}, 限制数量={limit}")
        
        # 使用SimilarityService进行相似度搜索
        results = similarity_service.search_by_similarity(
            search_text,
            data_source,
            columns,
            limit
        )
        
        logger.info(f"相似度搜索完成，结果数量: {len(results)}")
        
        # 添加序号列
        for index, item in enumerate(results, 1):
            item['序号'] = index
        
        return ApiResponse.success(
            data=results,
            message="相似度搜索成功",
            meta={"total": len(results), "data_source": data_source}
        )
        
    except (BadRequestError, ValidationError) as e:
        # 这些错误会被全局错误处理器捕获
        raise
    except Exception as e:
        logger.error(f"相似度搜索过程中发生错误: {str(e)}")
        raise InternalError(f"相似度搜索失败: {str(e)}")
