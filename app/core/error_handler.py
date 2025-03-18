"""
错误处理核心模块
定义自定义异常类和错误代码
"""

from typing import Any, Dict, Optional


class AppError(Exception):
    """应用基础异常类"""

    def __init__(
        self, message: str, code: int = 400, details: Optional[Any] = None
    ) -> None:
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


# 400 错误 - 客户端错误
class BadRequestError(AppError):
    """请求参数错误"""

    def __init__(
        self, message: str = "请求参数错误", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 400, details)


class ValidationError(AppError):
    """数据验证错误"""

    def __init__(
        self, message: str = "数据验证失败", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 400, details)


class AuthorizationError(AppError):
    """授权错误"""

    def __init__(
        self, message: str = "授权失败", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 401, details)


class ForbiddenError(AppError):
    """禁止访问错误"""

    def __init__(
        self, message: str = "禁止访问", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 403, details)


class NotFoundError(AppError):
    """资源不存在错误"""

    def __init__(
        self, message: str = "资源不存在", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 404, details)


# 500 错误 - 服务器错误
class InternalError(AppError):
    """内部服务器错误"""

    def __init__(
        self, message: str = "内部服务器错误", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 500, details)


class DatabaseError(AppError):
    """数据库错误"""

    def __init__(
        self, message: str = "数据库操作失败", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 500, details)


class ServiceError(AppError):
    """服务调用错误"""

    def __init__(
        self, message: str = "服务调用失败", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 500, details)


class FileOperationError(AppError):
    """文件操作错误"""

    def __init__(
        self, message: str = "文件操作失败", details: Optional[Any] = None
    ) -> None:
        super().__init__(message, 500, details)


# 错误代码映射
ERROR_CODES: Dict[int, str] = {
    # 客户端错误 (400-499)
    400: "请求参数错误",
    401: "未授权",
    403: "禁止访问",
    404: "资源不存在",
    405: "方法不允许",
    413: "请求实体过大",
    415: "不支持的媒体类型",
    429: "请求过于频繁",
    # 服务器错误 (500-599)
    500: "内部服务器错误",
    501: "功能未实现",
    502: "网关错误",
    503: "服务不可用",
    504: "网关超时",
}
