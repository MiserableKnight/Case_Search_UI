"""数据源路由的 JSON 安全性与 CORS 策略测试。

回归两个高危修复：
- /api/search 结果含 NaN 时不得输出非法 JSON 字面量
- CORS 不得对任意外站来源放行
"""

import json
from unittest.mock import patch

import pandas as pd
import pytest


def _reject_constant(value):
    """json.loads 的 parse_constant 钩子：遇到 NaN/Infinity 字面量直接报错。"""
    raise ValueError(f"非法 JSON 常量: {value}")


@pytest.mark.api
class TestSearchNanHandling:
    """/api/search 的 NaN 处理"""

    def test_search_nan_values_serialized_as_null(self, client, flask_app):
        """结果含 NaN 时应输出 null，且响应是严格合法的 JSON"""
        df = pd.DataFrame(
            {
                "问题描述": ["发动机故障", None],
                "机型": ["737", "777"],
            }
        )

        with patch.object(flask_app, "load_data_source", return_value=df):
            response = client.post(
                "/api/search",
                json={"data_source": "case", "search_levels": []},
                content_type="application/json",
            )

        assert response.status_code == 200
        # 严格解析：若响应中含裸 NaN 字面量会抛 ValueError
        data = json.loads(response.data, parse_constant=_reject_constant)
        assert data["status"] == "success"
        assert data["data"][0]["问题描述"] == "发动机故障"
        assert data["data"][1]["问题描述"] is None


@pytest.mark.api
class TestCorsPolicy:
    """CORS 必须收敛到本机来源"""

    def test_evil_origin_not_allowed(self, client):
        """任意外站来源不得获得跨域许可"""
        response = client.options(
            "/api/search",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert "Access-Control-Allow-Origin" not in response.headers

    def test_localhost_origin_allowed(self, client):
        """本机来源（Flask 服务端口）允许跨域"""
        response = client.options(
            "/api/search",
            headers={
                "Origin": "http://localhost:5000",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5000"
