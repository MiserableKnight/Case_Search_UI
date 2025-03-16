from flask import request, jsonify, current_app
from app.api import bp
import logging
import pandas as pd

logger = logging.getLogger(__name__)

@bp.route('/api/data_source_columns')
def get_data_source_columns():
    """获取所有数据源的列名"""
    try:
        # 定义各数据源的基础列
        base_columns = {
            'case': [
                '故障发生日期', '申请时间', '标题', '版本号', '问题描述', '答复详情', 
                '客户期望', 'ATA', '机号/MSN', '运营人', '服务请求单编号', '机型', '数据类型'
            ],
            'engineering': [
                '发布时间', '文件名称', '原因和说明', '文件类型', 'MSN有效性', 
                '原文文本', '机型', '数据类型'
            ],
            'manual': [
                '申请时间', '问题描述', '答复详情', '飞机序列号/注册号/运营人',
                '机型', '数据类型'
            ],
            'faults': [
                '日期', '问题描述', '排故措施', '运营人', '飞机序列号', '机号',
                '机型', '数据类型'
            ]
        }

        # 获取实际数据源的列
        columns = {}
        for source in current_app.config['DATA_SOURCES']:
            try:
                # 首先尝试从实际数据中获取列
                df = current_app.load_data_source(source)
                if df is not None:
                    columns[source] = df.columns.tolist()
                else:
                    # 如果无法加载数据，使用基础列定义
                    columns[source] = base_columns.get(source, [])
                
                # 确保列表不为空
                if not columns[source]:
                    columns[source] = base_columns.get(source, [])
                
                # 记录日志
                logger.info(f"数据源 {source} 的列: {columns[source]}")
                
            except Exception as e:
                logger.warning(f"获取数据源 {source} 的列名时出错: {str(e)}")
                # 使用基础列作为后备
                columns[source] = base_columns.get(source, [])

        # 验证返回的数据
        if not columns or not any(cols for cols in columns.values()):
            raise ValueError("无法获取任何数据源的列信息")

        return jsonify({
            'status': 'success',
            'columns': columns
        })

    except Exception as e:
        error_msg = f"获取数据源列名失败: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500


@bp.route('/api/data_types/<source>', methods=['GET'])
def get_data_types(source):
    """获取指定数据源的数据类型"""
    try:
        if source not in current_app.config['DATA_SOURCES']:
            return jsonify({
                'status': 'error',
                'message': '无效的数据源'
            }), 400
        
        df = current_app.load_data_source(source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {current_app.config["DATA_SOURCES"][source]}'
            }), 404
        
        logger.info(f"数据源 {source} 的列名: {df.columns.tolist()}")
        
        if '数据类型' not in df.columns:
            logger.warning(f"数据源 {source} 中没有找到'数据类型'列")
            return jsonify({
                'status': 'error',
                'message': f"数据源 {source} 中没有'数据类型'列"
            }), 500
        
        logger.info(f"数据源 {source} 的数据类型: {df['数据类型'].unique().tolist()}")
        
        data_types = sorted(df['数据类型'].unique().tolist())
        
        return jsonify({
            'status': 'success',
            'types': data_types
        })
    except Exception as e:
        logger.error(f"获取数据类型时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bp.route('/api/search', methods=['POST'])
def search():
    """搜索数据"""
    try:
        data = request.get_json()
        data_source = data.get('data_source', 'case')
        search_levels = data.get('search_levels', [])
        data_types = data.get('data_types', [])
        aircraft_types = data.get('aircraft_types', [])
        
        # 加载选定的数据源
        df = current_app.load_data_source(data_source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {current_app.config["DATA_SOURCES"][data_source]}'
            }), 404

        # 复制数据框以避免修改原始数据
        result_df = df.copy()
        
        # 首先按数据类型筛选
        if data_types:
            result_df = result_df[result_df['数据类型'].isin(data_types)]
            
        # 添加机型筛选
        if aircraft_types:
            result_df = result_df[result_df['机型'].isin(aircraft_types)]
        
        # 处理每个搜索层级
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
        
        # 添加序号列
        for index, item in enumerate(results, 1):
            item['序号'] = index
        
        return jsonify({
            'status': 'success',
            'data': results,
            'total': len(results)
        })
            
    except Exception as e:
        logger.error(f"搜索时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
