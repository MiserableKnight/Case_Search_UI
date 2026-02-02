"""
错误处理服务
提供统一的错误响应格式化和处理功能
"""

import logging
import traceback
from typing import Any

from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException

from app.core.error_handler import AppError

logger = logging.getLogger(__name__)


class ErrorService:
    """错误处理服务类"""

    @staticmethod
    def format_error_response(
        error: Exception, include_traceback: bool = False
    ) -> tuple[dict[str, Any], int]:
        """
        格式化错误响应

        Args:
            error: 异常对象
            include_traceback: 是否包含堆栈跟踪信息

        Returns:
            dict: 格式化的错误响应
        """
        # 默认错误信息
        status_code: int = 500
        error_type: str = error.__class__.__name__
        error_message: str = "内部服务器错误"
        error_details: Any = None

        # 处理自定义应用错误
        if isinstance(error, AppError):
            status_code = error.code
            error_message = error.message
            error_details = error.details

        # 处理Flask/Werkzeug HTTP异常
        elif isinstance(error, HTTPException):
            status_code = error.code or 500
            error_message = error.description or "HTTP错误"

        # 处理其他异常
        else:
            error_message = str(error) or "内部服务器错误"

        # 构建响应
        error_dict: dict[str, Any] = {
            "code": status_code,
            "type": error_type,
            "message": error_message,
        }

        # 添加详细信息（如果有）
        if error_details:
            error_dict["details"] = error_details

        # 在开发环境中添加堆栈跟踪
        if include_traceback or (
            hasattr(current_app, "config") and current_app.config.get("DEBUG", False)
        ):
            error_dict["traceback"] = traceback.format_exc()

        response: dict[str, Any] = {"status": "error", "error": error_dict}

        return response, status_code

    @staticmethod
    def handle_exception(error):
        """
        处理异常并返回适当的响应

        Args:
            error: 捕获的异常

        Returns:
            Response: Flask响应对象
        """
        # 记录错误日志
        if isinstance(error, AppError) and error.code < 500:
            # 客户端错误，使用info级别记录
            logger.info(f"客户端错误: {error.__class__.__name__} - {error.message}")
        else:
            # 服务器错误，使用error级别记录
            logger.error(f"服务器错误: {error.__class__.__name__} - {str(error)}")
            logger.error(traceback.format_exc())

        # 格式化错误响应
        response_data, status_code = ErrorService.format_error_response(error)

        # 返回JSON响应
        return jsonify(response_data), status_code
