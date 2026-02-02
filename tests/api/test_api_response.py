"""
API响应服务单元测试

测试ApiResponse类提供的各种响应格式
"""

import json

import pytest
from flask import Flask

from app.services.api_response import ApiResponse


@pytest.mark.api
class TestApiResponse:
    """ApiResponse测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

    # ==================== success测试 ====================

    def test_success_default(self):
        """测试默认成功响应"""
        with self.app.test_request_context():
            response = ApiResponse.success()
            data = json.loads(response.data)

            assert data["status"] == "success"
            assert data["message"] == "操作成功"
            assert "data" not in data

    def test_success_with_data(self):
        """测试带数据的成功响应"""
        test_data = {"id": 1, "name": "测试"}

        with self.app.test_request_context():
            response = ApiResponse.success(data=test_data)
            data = json.loads(response.data)

            assert data["status"] == "success"
            assert data["data"] == test_data

    def test_success_with_message(self):
        """测试自定义消息"""
        with self.app.test_request_context():
            response = ApiResponse.success(message="自定义消息")
            data = json.loads(response.data)

            assert data["message"] == "自定义消息"

    def test_success_with_meta(self):
        """测试带元数据的响应"""
        meta = {"total": 100, "page": 1}

        with self.app.test_request_context():
            response = ApiResponse.success(meta=meta)
            data = json.loads(response.data)

            assert data["meta"] == meta

    def test_success_with_all_parameters(self):
        """测试带所有参数的成功响应"""
        test_data = [{"id": 1}, {"id": 2}]
        meta = {"total": 2}

        with self.app.test_request_context():
            response = ApiResponse.success(data=test_data, message="获取成功", meta=meta)
            data = json.loads(response.data)

            assert data["status"] == "success"
            assert data["data"] == test_data
            assert data["message"] == "获取成功"
            assert data["meta"] == meta

    def test_success_with_empty_data(self):
        """测试空数据"""
        with self.app.test_request_context():
            response = ApiResponse.success(data=[])
            data = json.loads(response.data)

            assert "data" in data
            assert data["data"] == []

    # ==================== error测试 ====================

    def test_error_default(self):
        """测试默认错误响应"""
        with self.app.test_request_context():
            response, status_code = ApiResponse.error()
            data = json.loads(response.data)

            assert status_code == 400
            assert data["status"] == "error"
            assert data["error"]["message"] == "操作失败"
            assert data["error"]["code"] == 400

    def test_error_with_message(self):
        """测试自定义错误消息"""
        with self.app.test_request_context():
            response, status_code = ApiResponse.error(message="自定义错误")
            data = json.loads(response.data)

            assert data["error"]["message"] == "自定义错误"

    def test_error_with_code(self):
        """测试自定义错误代码"""
        with self.app.test_request_context():
            response, status_code = ApiResponse.error(code=404)
            data = json.loads(response.data)

            assert status_code == 404
            assert data["error"]["code"] == 404

    def test_error_with_details(self):
        """测试带详情的错误响应"""
        details = {"field": "email", "reason": "invalid format"}

        with self.app.test_request_context():
            response, status_code = ApiResponse.error(details=details)
            data = json.loads(response.data)

            assert data["error"]["details"] == details

    def test_error_all_parameters(self):
        """测试带所有参数的错误响应"""
        details = {"missing_fields": ["title", "content"]}

        with self.app.test_request_context():
            response, status_code = ApiResponse.error(
                message="缺少必需字段", code=400, details=details
            )
            data = json.loads(response.data)

            assert data["error"]["message"] == "缺少必需字段"
            assert data["error"]["code"] == 400
            assert data["error"]["details"] == details

    def test_error_404(self):
        """测试404错误"""
        with self.app.test_request_context():
            response, status_code = ApiResponse.error(message="资源不存在", code=404)

            assert status_code == 404

    def test_error_500(self):
        """测试500错误"""
        with self.app.test_request_context():
            response, status_code = ApiResponse.error(message="服务器内部错误", code=500)

            assert status_code == 500

    # ==================== paginated测试 ====================

    def test_paginated_default(self):
        """测试默认分页响应"""
        data = [{"id": 1}, {"id": 2}]

        with self.app.test_request_context():
            response = ApiResponse.paginated(data, page=1, per_page=10, total=2)
            response_data = json.loads(response.data)

            assert response_data["status"] == "success"
            assert response_data["data"] == data
            assert "meta" in response_data
            assert "pagination" in response_data["meta"]

    def test_paginated_pagination_info(self):
        """测试分页信息"""
        data = [{"id": i} for i in range(1, 6)]

        with self.app.test_request_context():
            response = ApiResponse.paginated(data=data, page=1, per_page=5, total=20)
            response_data = json.loads(response.data)

            pagination = response_data["meta"]["pagination"]
            assert pagination["page"] == 1
            assert pagination["per_page"] == 5
            assert pagination["total"] == 20
            assert pagination["total_pages"] == 4
            assert pagination["has_next"] is True
            assert pagination["has_prev"] is False

    def test_paginated_last_page(self):
        """测试最后一页"""
        data = [{"id": 1}]

        with self.app.test_request_context():
            response = ApiResponse.paginated(data=data, page=2, per_page=10, total=11)
            response_data = json.loads(response.data)

            pagination = response_data["meta"]["pagination"]
            assert pagination["has_next"] is False
            assert pagination["has_prev"] is True

    def test_paginated_custom_message(self):
        """测试自定义消息"""
        data = [{"id": 1}]

        with self.app.test_request_context():
            response = ApiResponse.paginated(
                data=data, page=1, per_page=10, total=1, message="查询成功"
            )
            response_data = json.loads(response.data)

            assert response_data["message"] == "查询成功"

    def test_paginated_zero_per_page(self):
        """测试per_page为0"""
        data = [{"id": 1}]

        with self.app.test_request_context():
            response = ApiResponse.paginated(data=data, page=1, per_page=0, total=1)
            response_data = json.loads(response.data)

            assert response_data["meta"]["pagination"]["total_pages"] == 0

    def test_paginated_empty_data(self):
        """测试空数据分页"""
        with self.app.test_request_context():
            response = ApiResponse.paginated(data=[], page=1, per_page=10, total=0)
            response_data = json.loads(response.data)

            assert response_data["data"] == []
            assert response_data["meta"]["pagination"]["total"] == 0

    # ==================== file_download测试 ====================

    def test_file_download_default(self, temp_output_dir):
        """测试默认文件下载"""
        # 创建测试文件
        test_file = temp_output_dir / "test.txt"
        test_file.write_text("测试内容")

        with self.app.test_request_context():
            response = ApiResponse.file_download(str(test_file))

            assert response.status_code == 200
            # 验证是文件下载响应
            assert "attachment" in response.headers.get("Content-Disposition", "")

    def test_file_download_with_filename(self, temp_output_dir):
        """测试带文件名的下载"""
        test_file = temp_output_dir / "test.txt"
        test_file.write_text("测试内容")

        with self.app.test_request_context():
            response = ApiResponse.file_download(str(test_file), "custom_name.txt")

            assert "custom_name.txt" in response.headers.get("Content-Disposition", "")

    # ==================== 边界条件测试 ====================

    def test_success_with_none_data(self):
        """测试data为None"""
        with self.app.test_request_context():
            response = ApiResponse.success(data=None)
            response_data = json.loads(response.data)

            assert "data" not in response_data

    def test_success_with_complex_data(self):
        """测试复杂数据结构"""
        complex_data = {
            "users": [
                {"id": 1, "name": "测试1"},
                {"id": 2, "name": "测试2"},
            ],
            "metadata": {
                "version": "1.0",
                "timestamp": "2023-01-01",
            },
        }

        with self.app.test_request_context():
            response = ApiResponse.success(data=complex_data)
            response_data = json.loads(response.data)

            assert response_data["data"] == complex_data

    def test_error_with_complex_details(self):
        """测试复杂错误详情"""
        complex_details = {
            "validation_errors": [
                {"field": "email", "message": "Invalid email format"},
                {"field": "password", "message": "Password too short"},
            ],
            "request_id": "abc-123",
        }

        with self.app.test_request_context():
            response, status_code = ApiResponse.error(details=complex_details)
            response_data = json.loads(response.data)

            assert response_data["error"]["details"] == complex_details


@pytest.mark.parametrize(
    "code,expected_status",
    [
        (200, 200),
        (400, 400),
        (401, 401),
        (403, 403),
        (404, 404),
        (500, 500),
    ],
)
def test_error_status_codes(code, expected_status):
    """参数化测试错误状态码"""
    app = Flask(__name__)
    with app.test_request_context():
        response, status_code = ApiResponse.error(code=code)
        assert status_code == expected_status


@pytest.mark.parametrize(
    "page,per_page,total,expected_total_pages",
    [
        (1, 10, 100, 10),
        (1, 20, 100, 5),
        (1, 15, 100, 7),
        (1, 10, 95, 10),
        (1, 10, 0, 0),
    ],
)
def test_paginated_total_pages_calculation(page, per_page, total, expected_total_pages):
    """参数化测试总页数计算"""
    app = Flask(__name__)
    with app.test_request_context():
        response = ApiResponse.paginated([], page, per_page, total)
        response_data = json.loads(response.data)

        assert response_data["meta"]["pagination"]["total_pages"] == expected_total_pages
