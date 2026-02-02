"""SensitiveWordManager单元测试"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.core.word_manager import SensitiveWordManager


class TestSensitiveWordManager:
    """SensitiveWordManager测试类"""

    def test_init_with_file_path(self):
        """测试使用文件路径初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            assert manager.file_path == file_path
            assert manager.categories == [
                "organizations",
                "aircraft",
                "locations",
                "registration_numbers",
                "other",
            ]
            assert isinstance(manager.words, dict)
            assert isinstance(manager.sorted_words, list)

    def test_init_creates_file_if_not_exists(self):
        """测试初始化时创建不存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "new_words.json"
            assert not file_path.exists()

            manager = SensitiveWordManager(str(file_path))

            assert file_path.exists()
            # 验证文件内容是空的类别结构
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                assert "organizations" in data
                assert "aircraft" in data

    def test_ensure_file_exists_creates_directory(self):
        """测试确保文件存在时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "test_words.json"
            assert not file_path.parent.exists()

            manager = SensitiveWordManager(str(file_path))

            assert file_path.parent.exists()
            assert file_path.exists()

    def test_load_words_from_existing_file(self):
        """测试从现有文件加载敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            test_data = {
                "organizations": [{"word": "测试航空", "added_time": "2023-01-01"}],
                "aircraft": [{"word": "ARJ21", "added_time": "2023-01-01"}],
                "locations": [],
                "registration_numbers": [],
                "other": [],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(test_data, f, ensure_ascii=False)

            manager = SensitiveWordManager(str(file_path))

            assert len(manager.words["organizations"]) == 1
            assert manager.words["organizations"][0]["word"] == "测试航空"
            assert len(manager.words["aircraft"]) == 1

    def test_load_words_from_nonexistent_file(self):
        """测试从不存在的文件加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nonexistent.json"

            manager = SensitiveWordManager(str(file_path))

            # 应该创建文件并使用默认空值
            assert all(len(words) == 0 for words in manager.words.values())

    def test_get_all_words(self):
        """测试获取所有敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            all_words = manager.get_all_words()

            assert isinstance(all_words, dict)
            assert "organizations" in all_words
            assert "aircraft" in all_words
            assert "locations" in all_words

    def test_get_all_words_preserves_order(self):
        """测试获取所有敏感词时保持顺序"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            all_words = manager.get_all_words()

            # 验证返回的顺序与categories定义一致
            categories = list(all_words.keys())
            assert categories == [
                "organizations",
                "aircraft",
                "locations",
                "registration_numbers",
                "other",
            ]

    def test_get_sorted_words(self):
        """测试获取按长度排序的敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            # 添加一些测试数据
            manager.words["organizations"] = [
                {"word": "短"},
                {"word": "中等长度"},
                {"word": "这是一个非常长的敏感词"},
            ]
            manager.sorted_words = manager._create_sorted_list()

            sorted_words = manager.get_sorted_words()

            assert len(sorted_words) == 3
            # 验证按长度降序排序
            assert len(sorted_words[0]) > len(sorted_words[1])
            assert len(sorted_words[1]) > len(sorted_words[2])

    def test_create_sorted_list(self):
        """测试创建排序列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.words["organizations"] = [
                {"word": "AB"},
                {"word": "A"},
                {"word": "ABC"},
            ]
            manager.words["aircraft"] = [
                {"word": "ABCD"},
            ]

            sorted_list = manager._create_sorted_list()

            assert len(sorted_list) == 4
            assert sorted_list[0] == "ABCD"  # 最长
            assert sorted_list[-1] == "A"  # 最短

    def test_add_word_success(self):
        """测试成功添加敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.add_word("测试航空公司", "organizations")

            assert success is True
            assert "已添加" in message
            assert len(manager.words["organizations"]) == 1
            assert manager.words["organizations"][0]["word"] == "测试航空公司"

    def test_add_word_empty(self):
        """测试添加空敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.add_word("", "organizations")

            assert success is False
            assert "不能为空" in message

    def test_add_word_whitespace_only(self):
        """测试添加只有空格的敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.add_word("   ", "organizations")

            assert success is False
            assert "不能为空" in message

    def test_add_word_invalid_category(self):
        """测试添加到无效类别"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.add_word("测试", "invalid_category")

            assert success is False
            assert "不存在" in message

    def test_add_duplicate_word(self):
        """测试添加重复敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("测试词", "organizations")
            success, message = manager.add_word("测试词", "organizations")

            assert success is False
            assert "已存在" in message
            assert len(manager.words["organizations"]) == 1

    def test_add_word_updates_sorted_list(self):
        """测试添加敏感词后更新排序列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("短", "organizations")
            manager.add_word("非常长的敏感词", "organizations")

            sorted_words = manager.get_sorted_words()
            assert len(sorted_words) == 2
            assert sorted_words[0] == "非常长的敏感词"

    def test_remove_word_success(self):
        """测试成功删除敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("测试词", "organizations")
            assert len(manager.words["organizations"]) == 1

            success, message = manager.remove_word("测试词", "organizations")

            assert success is True
            assert "删除" in message
            assert len(manager.words["organizations"]) == 0

    def test_remove_word_invalid_category(self):
        """测试从无效类别删除"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.remove_word("测试", "invalid")

            assert success is False
            assert "不存在" in message

    def test_remove_word_not_found(self):
        """测试删除不存在的敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.remove_word("不存在的词", "organizations")

            assert success is False
            assert "未找到" in message

    def test_remove_word_updates_sorted_list(self):
        """测试删除敏感词后更新排序列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("测试词", "organizations")
            assert "测试词" in manager.sorted_words

            manager.remove_word("测试词", "organizations")

            assert "测试词" not in manager.sorted_words

    def test_get_words_by_category(self):
        """测试按类别获取敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("航空公司1", "organizations")
            manager.add_word("航空公司2", "organizations")

            words = manager.get_words_by_category("organizations")

            assert len(words) == 2
            assert words[0]["word"] == "航空公司1"

    def test_get_words_by_invalid_category(self):
        """测试从无效类别获取敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            words = manager.get_words_by_category("invalid")

            assert words == []

    def test_save_words(self):
        """测试保存敏感词到文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("测试词", "organizations")

            # 验证文件被保存
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                assert len(data["organizations"]) == 1
                assert data["organizations"][0]["word"] == "测试词"

    def test_category_labels(self):
        """测试类别标签"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            assert manager.category_labels["organizations"] == "组织机构"
            assert manager.category_labels["aircraft"] == "设备型号"
            assert manager.category_labels["locations"] == "地点"

    def test_add_word_trims_whitespace(self):
        """测试添加敏感词时去除空格"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            success, message = manager.add_word("  测试词  ", "organizations")

            assert success is True
            assert manager.words["organizations"][0]["word"] == "测试词"

    def test_add_multiple_words_to_different_categories(self):
        """测试向不同类别添加多个敏感词"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_words.json"
            manager = SensitiveWordManager(str(file_path))

            manager.add_word("航空公司", "organizations")
            manager.add_word("ARJ21", "aircraft")
            manager.add_word("北京", "locations")

            assert len(manager.words["organizations"]) == 1
            assert len(manager.words["aircraft"]) == 1
            assert len(manager.words["locations"]) == 1

            sorted_words = manager.get_sorted_words()
            assert len(sorted_words) == 3
