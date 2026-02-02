"""
相似度API端点集成测试

测试相似度计算相关的API路由
"""

import json
from unittest.mock import patch

import pytest


@pytest.mark.api
class TestSimilarityRoutes:
    """相似度API路由测试类"""

    # ==================== /api/similarity 测试 ====================

    def test_calculate_text_similarity_success(self, client, sample_similarity_data):
        """测试成功计算文本相似度"""
        # Mock SimilarityService
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.calculate_batch_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity",
                json={
                    "text": "发动机故障",
                    "columns": ["标题", "问题描述"],
                    "results": sample_similarity_data,
                },
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "data" in data

    def test_calculate_text_similarity_missing_data(self, client):
        """测试缺少请求数据"""
        response = client.post(
            "/api/similarity",
            data="",
            content_type="application/json",
        )

        # 应该返回错误
        assert response.status_code in [400, 500]

    def test_calculate_text_similarity_missing_text_field(self, client, sample_similarity_data):
        """测试缺少text字段"""
        response = client.post(
            "/api/similarity",
            json={
                "columns": ["标题"],
                "results": sample_similarity_data,
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_calculate_text_similarity_missing_columns_field(self, client, sample_similarity_data):
        """测试缺少columns字段"""
        response = client.post(
            "/api/similarity",
            json={
                "text": "发动机故障",
                "results": sample_similarity_data,
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_calculate_text_similarity_missing_results_field(self, client):
        """测试缺少results字段"""
        response = client.post(
            "/api/similarity",
            json={
                "text": "发动机故障",
                "columns": ["标题"],
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_calculate_text_similarity_adds_sequence_number(self, client, sample_similarity_data):
        """测试添加序号列"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.calculate_batch_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity",
                json={
                    "text": "发动机故障",
                    "columns": ["标题"],
                    "results": sample_similarity_data,
                },
                content_type="application/json",
            )

            data = json.loads(response.data)
            results = data["data"]
            # 检查序号是否添加
            assert "序号" in results[0]
            assert results[0]["序号"] == 1
            assert results[1]["序号"] == 2

    def test_calculate_text_similarity_service_error(self, client, sample_similarity_data):
        """测试服务层错误"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.calculate_batch_similarity.side_effect = Exception("服务错误")

            response = client.post(
                "/api/similarity",
                json={
                    "text": "发动机故障",
                    "columns": ["标题"],
                    "results": sample_similarity_data,
                },
                content_type="application/json",
            )

            # 应该返回500错误
            assert response.status_code == 500

    # ==================== /api/similarity_search 测试 ====================

    def test_similarity_search_success(self, client, sample_similarity_data):
        """测试成功相似度搜索"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.search_by_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity_search",
                json={
                    "text": "发动机故障",
                    "dataSource": "test_source",
                    "columns": ["标题", "问题描述"],
                    "limit": 10,
                },
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "data" in data
            assert "meta" in data

    def test_similarity_search_missing_data(self, client):
        """测试缺少请求数据"""
        response = client.post(
            "/api/similarity_search",
            data="",
            content_type="application/json",
        )

        assert response.status_code in [400, 500]

    def test_similarity_search_missing_text_field(self, client):
        """测试缺少text字段"""
        response = client.post(
            "/api/similarity_search",
            json={
                "dataSource": "test",
                "columns": ["标题"],
                "limit": 10,
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_similarity_search_missing_dataSource_field(self, client):
        """测试缺少dataSource字段"""
        response = client.post(
            "/api/similarity_search",
            json={
                "text": "发动机",
                "columns": ["标题"],
                "limit": 10,
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_similarity_search_missing_columns_field(self, client):
        """测试缺少columns字段"""
        response = client.post(
            "/api/similarity_search",
            json={
                "text": "发动机",
                "dataSource": "test",
                "limit": 10,
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_similarity_search_missing_limit_field(self, client):
        """测试缺少limit字段"""
        response = client.post(
            "/api/similarity_search",
            json={
                "text": "发动机",
                "dataSource": "test",
                "columns": ["标题"],
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_similarity_search_returns_meta(self, client, sample_similarity_data):
        """测试返回meta信息"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.search_by_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity_search",
                json={
                    "text": "发动机故障",
                    "dataSource": "case",
                    "columns": ["标题"],
                    "limit": 10,
                },
                content_type="application/json",
            )

            data = json.loads(response.data)
            assert "meta" in data
            assert data["meta"]["total"] == len(sample_similarity_data)
            assert data["meta"]["data_source"] == "case"

    def test_similarity_search_adds_sequence_number(self, client, sample_similarity_data):
        """测试添加序号列"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.search_by_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity_search",
                json={
                    "text": "发动机故障",
                    "dataSource": "case",
                    "columns": ["标题"],
                    "limit": 10,
                },
                content_type="application/json",
            )

            data = json.loads(response.data)
            results = data["data"]
            assert "序号" in results[0]
            assert results[0]["序号"] == 1

    def test_similarity_search_service_error(self, client):
        """测试服务层错误"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.search_by_similarity.side_effect = Exception("搜索失败")

            response = client.post(
                "/api/similarity_search",
                json={
                    "text": "发动机",
                    "dataSource": "case",
                    "columns": ["标题"],
                    "limit": 10,
                },
                content_type="application/json",
            )

            assert response.status_code == 500

    # ==================== 边界条件测试 ====================

    def test_calculate_similarity_empty_results(self, client):
        """测试空结果列表"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.calculate_batch_similarity.return_value = []

            response = client.post(
                "/api/similarity",
                json={
                    "text": "发动机",
                    "columns": ["标题"],
                    "results": [],
                },
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["data"] == []

    def test_similarity_search_zero_limit(self, client, sample_similarity_data):
        """测试limit为0"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.search_by_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity_search",
                json={
                    "text": "发动机",
                    "dataSource": "case",
                    "columns": ["标题"],
                    "limit": 0,
                },
                content_type="application/json",
            )

            assert response.status_code == 200

    def test_similarity_search_large_limit(self, client, sample_similarity_data):
        """测试大limit值"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.search_by_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity_search",
                json={
                    "text": "发动机",
                    "dataSource": "case",
                    "columns": ["标题"],
                    "limit": 10000,
                },
                content_type="application/json",
            )

            assert response.status_code == 200

    def test_calculate_similarity_very_long_text(self, client, sample_similarity_data):
        """测试超长文本"""
        long_text = "测试 " * 10000

        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.calculate_batch_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity",
                json={
                    "text": long_text,
                    "columns": ["标题"],
                    "results": sample_similarity_data,
                },
                content_type="application/json",
            )

            assert response.status_code == 200

    def test_calculate_similarity_special_characters(self, client, sample_similarity_data):
        """测试特殊字符"""
        with patch("app.api.similarity_routes.similarity_service") as mock_service:
            mock_service.calculate_batch_similarity.return_value = sample_similarity_data

            response = client.post(
                "/api/similarity",
                json={
                    "text": "测试！@#￥%……&*（）",
                    "columns": ["标题"],
                    "results": sample_similarity_data,
                },
                content_type="application/json",
            )

            assert response.status_code == 200


@pytest.mark.parametrize(
    "missing_field",
    [
        "text",
        "columns",
        "results",
    ],
)
def test_calculate_similarity_missing_fields(client, missing_field, sample_similarity_data):
    """参数化测试缺少字段"""
    payload = {
        "text": "测试",
        "columns": ["标题"],
        "results": sample_similarity_data,
    }
    del payload[missing_field]

    response = client.post(
        "/api/similarity",
        json=payload,
        content_type="application/json",
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "missing_field",
    [
        "text",
        "dataSource",
        "columns",
        "limit",
    ],
)
def test_similarity_search_missing_fields(client, missing_field):
    """参数化测试缺少字段"""
    payload = {
        "text": "测试",
        "dataSource": "case",
        "columns": ["标题"],
        "limit": 10,
    }
    del payload[missing_field]

    response = client.post(
        "/api/similarity_search",
        json=payload,
        content_type="application/json",
    )

    assert response.status_code == 400
