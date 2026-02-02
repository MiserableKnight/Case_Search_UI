"""
错误处理类单元测试

测试自定义异常类的各种功能
"""

import pytest

from app.core.error_handler import (
    ERROR_CODES,
    AppError,
    AuthorizationError,
    BadRequestError,
    DatabaseError,
    FileOperationError,
    ForbiddenError,
    InternalError,
    NotFoundError,
    ServiceError,
    ValidationError,
)


class TestAppError:
    """AppError基础异常类测试"""

    def test_app_error_basic(self):
        """测试基础异常"""
        error = AppError("错误消息")
        assert error.message == "错误消息"
        assert error.code == 400  # 默认状态码
        assert error.details is None
        assert str(error) == "错误消息"

    def test_app_error_with_code(self):
        """测试带状态码的异常"""
        error = AppError("错误消息", code=500)
        assert error.message == "错误消息"
        assert error.code == 500

    def test_app_error_with_details(self):
        """测试带详情的异常"""
        details = {"field": "username", "reason": "already exists"}
        error = AppError("错误消息", details=details)
        assert error.details == details

    def test_app_error_all_parameters(self):
        """测试所有参数"""
        error = AppError("错误消息", code=404, details={"id": 123})
        assert error.message == "错误消息"
        assert error.code == 404
        assert error.details == {"id": 123}

    def test_app_error_raise_and_catch(self):
        """测试抛出和捕获异常"""
        with pytest.raises(AppError) as exc_info:
            raise AppError("测试错误")

        assert str(exc_info.value) == "测试错误"
        assert exc_info.value.message == "测试错误"


class TestBadRequestError:
    """BadRequestError测试"""

    def test_bad_request_default(self):
        """测试默认BadRequestError"""
        error = BadRequestError()
        assert error.message == "请求参数错误"
        assert error.code == 400

    def test_bad_request_custom_message(self):
        """测试自定义消息"""
        error = BadRequestError("无效的输入参数")
        assert error.message == "无效的输入参数"
        assert error.code == 400

    def test_bad_request_with_details(self):
        """测试带详情"""
        details = {"field": "email", "issue": "invalid format"}
        error = BadRequestError("邮箱格式错误", details=details)
        assert error.code == 400
        assert error.details == details


class TestValidationError:
    """ValidationError测试"""

    def test_validation_default(self):
        """测试默认ValidationError"""
        error = ValidationError()
        assert error.message == "数据验证失败"
        assert error.code == 400

    def test_validation_custom_message(self):
        """测试自定义消息"""
        error = ValidationError("年龄必须大于0")
        assert error.message == "年龄必须大于0"

    def test_validation_with_details(self):
        """测试带详情的验证错误"""
        details = {
            "field": "password",
            "constraints": ["min_length: 8", "must_contain_special_char"],
        }
        error = ValidationError("密码不符合要求", details=details)
        assert error.code == 400
        assert error.details == details


class TestAuthorizationError:
    """AuthorizationError测试"""

    def test_authorization_default(self):
        """测试默认AuthorizationError"""
        error = AuthorizationError()
        assert error.message == "授权失败"
        assert error.code == 401

    def test_authorization_custom_message(self):
        """测试自定义消息"""
        error = AuthorizationError("Token已过期")
        assert error.message == "Token已过期"
        assert error.code == 401


class TestForbiddenError:
    """ForbiddenError测试"""

    def test_forbidden_default(self):
        """测试默认ForbiddenError"""
        error = ForbiddenError()
        assert error.message == "禁止访问"
        assert error.code == 403

    def test_forbidden_custom_message(self):
        """测试自定义消息"""
        error = ForbiddenError("权限不足")
        assert error.message == "权限不足"
        assert error.code == 403


class TestNotFoundError:
    """NotFoundError测试"""

    def test_not_found_default(self):
        """测试默认NotFoundError"""
        error = NotFoundError()
        assert error.message == "资源不存在"
        assert error.code == 404

    def test_not_found_custom_message(self):
        """测试自定义消息"""
        error = NotFoundError("用户不存在")
        assert error.message == "用户不存在"
        assert error.code == 404

    def test_not_found_with_details(self):
        """测试带详情的404错误"""
        error = NotFoundError("数据不存在", details={"resource_type": "Case", "id": 123})
        assert error.code == 404
        assert error.details["resource_type"] == "Case"


class TestInternalError:
    """InternalError测试"""

    def test_internal_default(self):
        """测试默认InternalError"""
        error = InternalError()
        assert error.message == "内部服务器错误"
        assert error.code == 500

    def test_internal_custom_message(self):
        """测试自定义消息"""
        error = InternalError("数据库连接失败")
        assert error.message == "数据库连接失败"
        assert error.code == 500


class TestDatabaseError:
    """DatabaseError测试"""

    def test_database_default(self):
        """测试默认DatabaseError"""
        error = DatabaseError()
        assert error.message == "数据库操作失败"
        assert error.code == 500

    def test_database_custom_message(self):
        """测试自定义消息"""
        error = DatabaseError("插入数据失败")
        assert error.message == "插入数据失败"
        assert error.code == 500

    def test_database_with_details(self):
        """测试带详情的数据库错误"""
        details = {"query": "SELECT * FROM users", "error_code": "ORA-12154"}
        error = DatabaseError("查询执行失败", details=details)
        assert error.code == 500
        assert "query" in error.details


class TestServiceError:
    """ServiceError测试"""

    def test_service_default(self):
        """测试默认ServiceError"""
        error = ServiceError()
        assert error.message == "服务调用失败"
        assert error.code == 500

    def test_service_custom_message(self):
        """测试自定义消息"""
        error = ServiceError("支付服务不可用")
        assert error.message == "支付服务不可用"
        assert error.code == 500


class TestFileOperationError:
    """FileOperationError测试"""

    def test_file_operation_default(self):
        """测试默认FileOperationError"""
        error = FileOperationError()
        assert error.message == "文件操作失败"
        assert error.code == 500

    def test_file_operation_custom_message(self):
        """测试自定义消息"""
        error = FileOperationError("文件读取失败")
        assert error.message == "文件读取失败"
        assert error.code == 500

    def test_file_operation_with_details(self):
        """测试带详情的文件操作错误"""
        details = {"file_path": "/path/to/file.txt", "operation": "read"}
        error = FileOperationError("无法打开文件", details=details)
        assert error.code == 500
        assert error.details["file_path"] == "/path/to/file.txt"


class TestErrorCodes:
    """ERROR_CODES常量测试"""

    def test_error_codes_is_dict(self):
        """测试ERROR_CODES是字典"""
        assert isinstance(ERROR_CODES, dict)

    def test_error_codes_contains_client_errors(self):
        """测试包含客户端错误代码"""
        assert 400 in ERROR_CODES
        assert 401 in ERROR_CODES
        assert 403 in ERROR_CODES
        assert 404 in ERROR_CODES

    def test_error_codes_contains_server_errors(self):
        """测试包含服务器错误代码"""
        assert 500 in ERROR_CODES
        assert 502 in ERROR_CODES
        assert 503 in ERROR_CODES
        assert 504 in ERROR_CODES

    def test_error_code_messages(self):
        """测试错误代码消息"""
        assert ERROR_CODES[400] == "请求参数错误"
        assert ERROR_CODES[404] == "资源不存在"
        assert ERROR_CODES[500] == "内部服务器错误"


class TestErrorHandlingPatterns:
    """错误处理模式测试"""

    def test_raise_and_catch_specific_error(self):
        """测试抛出和捕获特定错误"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("测试验证错误")

        error = exc_info.value
        assert error.code == 400
        assert isinstance(error, AppError)

    def test_catch_as_base_error(self):
        """测试作为基类捕获"""
        with pytest.raises(AppError) as exc_info:
            raise BadRequestError("错误消息")

        assert isinstance(exc_info.value, BadRequestError)

    def test_error_inheritance_chain(self):
        """测试错误继承链"""
        error = ValidationError("测试")
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)

    def test_error_with_none_details(self):
        """测试详情为None的情况"""
        error = ServiceError("错误", details=None)
        assert error.details is None

    def test_error_with_empty_details(self):
        """测试详情为空字典的情况"""
        error = NotFoundError("未找到", details={})
        assert error.details == {}

    def test_error_with_complex_details(self):
        """测试复杂详情结构"""
        details = {
            "errors": [
                {"field": "email", "message": "Invalid email"},
                {"field": "password", "message": "Too short"},
            ],
            "timestamp": "2023-01-01T00:00:00",
            "request_id": "abc-123",
        }
        error = BadRequestError("多个验证错误", details=details)
        assert len(error.details["errors"]) == 2


@pytest.mark.parametrize(
    "error_class,expected_code",
    [
        (BadRequestError, 400),
        (ValidationError, 400),
        (AuthorizationError, 401),
        (ForbiddenError, 403),
        (NotFoundError, 404),
        (InternalError, 500),
        (DatabaseError, 500),
        (ServiceError, 500),
        (FileOperationError, 500),
    ],
)
def test_error_status_codes(error_class, expected_code):
    """参数化测试错误状态码"""
    error = error_class()
    assert error.code == expected_code


@pytest.mark.parametrize(
    "error_class,message",
    [
        (BadRequestError, "Bad request"),
        (ValidationError, "Validation failed"),
        (NotFoundError, "Not found"),
        (InternalError, "Internal error"),
    ],
)
def test_error_messages(error_class, message):
    """参数化测试错误消息"""
    error = error_class(message)
    assert error.message == message
    assert str(error) == message
