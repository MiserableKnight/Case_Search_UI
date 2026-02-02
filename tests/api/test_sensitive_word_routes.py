"""sensitive_word_routes API测试"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


class TestGetSensitiveWords:
    """GET /sensitive_words 路由测试"""

    def test_get_sensitive_words_success(self, client):
        """测试成功获取敏感词列表"""
        response = client.get("/api/sensitive_words")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "words" in data
        assert isinstance(data["words"], dict)

    def test_get_sensitive_words_structure(self, client):
        """测试敏感词列表结构"""
        response = client.get("/api/sensitive_words")

        data = response.get_json()
        words = data["words"]

        # 验证包含所有类别
        assert "organizations" in words
        assert "aircraft" in words
        assert "locations" in words
        assert "registration_numbers" in words
        assert "other" in words


class TestAddSensitiveWord:
    """POST /sensitive_words 路由测试"""

    def test_add_sensitive_word_success(self, client):
        """测试成功添加敏感词"""
        payload = {"word": "测试航空公司", "category": "organizations"}

        response = client.post("/api/sensitive_words", json=payload)

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "已添加" in data["message"]

    def test_add_sensitive_word_missing_word(self, client):
        """测试缺少word字段"""
        payload = {"category": "organizations"}

        response = client.post("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "无效的请求数据" in data["message"]

    def test_add_sensitive_word_missing_category(self, client):
        """测试缺少category字段"""
        payload = {"word": "测试词"}

        response = client.post("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_add_sensitive_word_empty_data(self, client):
        """测试空请求数据"""
        # json=None会导致500错误,因为request.get_json()失败
        # 这是正确的行为,因为Content-Type不是application/json
        response = client.post("/api/sensitive_words", json=None)

        # 应该返回500,因为服务器端处理json=None时出错
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"

    def test_add_sensitive_word_empty_json(self, client):
        """测试空JSON对象"""
        response = client.post("/api/sensitive_words", json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_add_sensitive_word_empty_word(self, client):
        """测试添加空敏感词"""
        payload = {"word": "", "category": "organizations"}

        response = client.post("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_add_sensitive_word_invalid_category(self, client):
        """测试添加到无效类别"""
        payload = {"word": "测试词", "category": "invalid_category"}

        response = client.post("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "不存在" in data["message"]

    def test_add_duplicate_sensitive_word(self, client):
        """测试添加重复敏感词"""
        payload = {"word": "重复词", "category": "organizations"}

        # 第一次添加
        response1 = client.post("/api/sensitive_words", json=payload)
        assert response1.status_code == 200

        # 第二次添加相同的词
        response2 = client.post("/api/sensitive_words", json=payload)
        assert response2.status_code == 400
        data = response2.get_json()
        assert "已存在" in data["message"]

    def test_add_sensitive_word_all_categories(self, client):
        """测试向所有类别添加敏感词"""
        categories = ["organizations", "aircraft", "locations", "registration_numbers", "other"]

        for category in categories:
            payload = {"word": f"测试{category}", "category": category}
            response = client.post("/api/sensitive_words", json=payload)
            assert response.status_code == 200, f"Failed for category {category}"


class TestRemoveSensitiveWord:
    """DELETE /sensitive_words 路由测试"""

    def test_remove_sensitive_word_success(self, client):
        """测试成功删除敏感词"""
        # 先添加一个敏感词
        add_payload = {"word": "待删除词", "category": "organizations"}
        add_response = client.post("/api/sensitive_words", json=add_payload)
        assert add_response.status_code == 200

        # 然后删除它
        remove_payload = {"word": "待删除词", "category": "organizations"}
        remove_response = client.delete("/api/sensitive_words", json=remove_payload)

        assert remove_response.status_code == 200
        data = remove_response.get_json()
        assert data["status"] == "success"
        assert "删除" in data["message"]

    def test_remove_sensitive_word_missing_word(self, client):
        """测试删除时缺少word字段"""
        payload = {"category": "organizations"}

        response = client.delete("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_remove_sensitive_word_missing_category(self, client):
        """测试删除时缺少category字段"""
        payload = {"word": "测试词"}

        response = client.delete("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_remove_sensitive_word_empty_data(self, client):
        """测试删除时空请求数据"""
        # json=None会导致500错误
        response = client.delete("/api/sensitive_words", json=None)

        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"

    def test_remove_sensitive_word_invalid_category(self, client):
        """测试从无效类别删除"""
        payload = {"word": "测试词", "category": "invalid"}

        response = client.delete("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "不存在" in data["message"]

    def test_remove_nonexistent_word(self, client):
        """测试删除不存在的敏感词"""
        payload = {"word": "不存在的词", "category": "organizations"}

        response = client.delete("/api/sensitive_words", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "未找到" in data["message"]

    def test_remove_sensitive_word_from_different_categories(self, client):
        """测试从不同类别删除敏感词"""
        # 添加到不同类别
        categories = ["organizations", "aircraft", "locations"]

        for category in categories:
            # 添加
            word = f"test_{category}_word"
            add_payload = {"word": word, "category": category}
            client.post("/api/sensitive_words", json=add_payload)

            # 删除
            remove_payload = {"word": word, "category": category}
            remove_response = client.delete("/api/sensitive_words", json=remove_payload)
            assert remove_response.status_code == 200, f"Failed to remove from {category}"
