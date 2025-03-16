from flask import request, jsonify, current_app
from app.api import bp
import logging

logger = logging.getLogger(__name__)

@bp.route('/sensitive_words', methods=['GET'])
def get_sensitive_words():
    """获取敏感词列表"""
    try:
        word_manager = current_app.word_manager
        words = word_manager.get_all_words()
        return jsonify({
            'status': 'success',
            'words': words
        })
    except Exception as e:
        logger.error(f"获取敏感词列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取敏感词列表失败: {str(e)}'
        }), 500


@bp.route('/sensitive_words', methods=['POST'])
def add_sensitive_word():
    """添加敏感词"""
    try:
        data = request.get_json()
        if not data or 'word' not in data or 'category' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400

        word = data['word']
        category = data['category']
        
        word_manager = current_app.word_manager
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
        logger.error(f"添加敏感词失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'添加敏感词失败: {str(e)}'
        }), 500


@bp.route('/sensitive_words', methods=['DELETE'])
def remove_sensitive_word():
    """删除敏感词"""
    try:
        data = request.get_json()
        if not data or 'word' not in data or 'category' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400

        word = data['word']
        category = data['category']
        
        word_manager = current_app.word_manager
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
        logger.error(f"删除敏感词失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'删除敏感词失败: {str(e)}'
        }), 500
