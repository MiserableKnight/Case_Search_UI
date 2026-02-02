"""
API响应服务
提供统一的API响应格式化功能
"""

from typing import Any

from flask import jsonify


class ApiResponse:
    """API响应格式化工具类"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功", meta: Any = None):
        """
        成功响应

        Args:
            data: 响应数据
            message: 成功消息
            meta: 元数据，如分页信息

        Returns:
            Response: Flask响应对象
        """
        response = {"status": "success", "message": message}

        if data is not None:
            response["data"] = data

        if meta is not None:
            response["meta"] = meta

        return jsonify(response)

    @staticmethod
    def error(message: str = "操作失败", code: int = 400, details: Any = None):
        """
        错误响应

        Args:
            message: 错误消息
            code: HTTP状态码
            details: 错误详情

        Returns:
            tuple: (Response, status_code)
        """
        error_dict: dict[str, Any] = {"code": code, "message": message}

        if details is not None:
            error_dict["details"] = details

        response: dict[str, Any] = {"status": "error", "error": error_dict}

        return jsonify(response), code

    @staticmethod
    def paginated(data, page, per_page, total, message="获取数据成功"):
        """
        分页响应

        Args:
            data: 分页数据
            page: 当前页码
            per_page: 每页条数
            total: 总记录数
            message: 成功消息

        Returns:
            Response: Flask响应对象
        """
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        meta = {
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

        return ApiResponse.success(data, message, meta)

    @staticmethod
    def file_download(file_path, filename=None):
        """
        文件下载响应

        Args:
            file_path: 文件路径
            filename: 下载文件名

        Returns:
            Response: Flask响应对象
        """
        from flask import send_file

        if filename:
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return send_file(file_path, as_attachment=True)
