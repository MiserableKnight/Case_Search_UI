"""file_handlers单元测试"""

import json
import os
import tempfile
from unittest.mock import Mock

from app.utils import file_handlers


class TestAllowedFile:
    """allowed_file函数测试"""

    def test_allowed_file_xlsx(self):
        """测试xlsx文件扩展名"""
        assert file_handlers.allowed_file("test.xlsx") is True

    def test_allowed_file_xls(self):
        """测试xls文件扩展名"""
        assert file_handlers.allowed_file("test.xls") is True

    def test_allowed_file_uppercase(self):
        """测试大写扩展名"""
        assert file_handlers.allowed_file("test.XLSX") is True
        assert file_handlers.allowed_file("test.XLS") is True

    def test_allowed_file_mixed_case(self):
        """测试混合大小写扩展名"""
        assert file_handlers.allowed_file("test.Xlsx") is True
        assert file_handlers.allowed_file("test.XlS") is True

    def test_allowed_file_invalid_extension(self):
        """测试无效文件扩展名"""
        assert file_handlers.allowed_file("test.txt") is False
        assert file_handlers.allowed_file("test.pdf") is False
        assert file_handlers.allowed_file("test.csv") is False

    def test_allowed_file_no_extension(self):
        """测试没有扩展名的文件"""
        assert file_handlers.allowed_file("test") is False

    def test_allowed_file_multiple_dots(self):
        """测试多个点的文件名"""
        assert file_handlers.allowed_file("test.file.xlsx") is True
        assert file_handlers.allowed_file("test.file.txt") is False

    def test_allowed_file_empty_string(self):
        """测试空字符串"""
        assert file_handlers.allowed_file("") is False


class TestSaveTempFile:
    """save_temp_file函数测试"""

    def test_save_temp_file_success(self):
        """测试成功保存临时文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 临时替换UPLOAD_FOLDER
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                # 创建mock文件对象
                mock_file = Mock()
                mock_file.filename = "test_file.xlsx"

                # 创建临时文件内容
                temp_content = b"test content"
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(temp_content)
                    temp_file_path = tmp.name

                # Mock save方法
                def mock_save(path):
                    import shutil

                    shutil.copy(temp_file_path, path)
                    os.unlink(temp_file_path)

                mock_file.save = mock_save

                # 调用函数
                temp_id, temp_path = file_handlers.save_temp_file(mock_file, "test_source")

                # 验证结果
                assert temp_id is not None
                assert temp_path is not None
                assert os.path.exists(temp_path)
                assert temp_path.startswith(tmpdir)

                # 验证文件名格式
                filename = os.path.basename(temp_path)
                assert filename.startswith(f"{temp_id}_")
                assert filename.endswith("test_file.xlsx")

            finally:
                file_handlers.UPLOAD_FOLDER = original_folder

    def test_save_temp_file_with_custom_filename(self):
        """测试使用自定义文件名"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                mock_file = Mock()
                mock_file.filename = "original.xlsx"

                def mock_save(path):
                    with open(path, "wb") as f:
                        f.write(b"test")

                mock_file.save = mock_save

                temp_id, temp_path = file_handlers.save_temp_file(
                    mock_file, "test_source", custom_filename="custom.xlsx"
                )

                assert temp_path.endswith("custom.xlsx")

            finally:
                file_handlers.UPLOAD_FOLDER = original_folder

    def test_save_temp_file_secures_filename(self):
        """测试文件名安全处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                mock_file = Mock()
                mock_file.filename = "../../../malicious.xlsx"

                def mock_save(path):
                    with open(path, "wb") as f:
                        f.write(b"test")

                mock_file.save = mock_save

                temp_id, temp_path = file_handlers.save_temp_file(mock_file, "test_source")

                # 验证路径中没有..目录遍历
                assert ".." not in temp_path
                assert os.path.exists(temp_path)

            finally:
                file_handlers.UPLOAD_FOLDER = original_folder


class TestSaveTempInfo:
    """save_temp_info函数测试"""

    def test_save_temp_info_success(self):
        """测试成功保存临时信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                temp_id = "test_id_123"
                temp_path = "/path/to/file.xlsx"
                data_source = "test_source"
                processor_type = "test_processor"

                file_handlers.save_temp_info(temp_id, temp_path, data_source, processor_type)

                # 验证info文件被创建
                info_path = os.path.join(tmpdir, f"{temp_id}_info.json")
                assert os.path.exists(info_path)

                # 验证文件内容
                with open(info_path, encoding="utf-8") as f:
                    data = json.load(f)

                assert data["temp_id"] == temp_id
                assert data["file_path"] == temp_path
                assert data["data_source"] == data_source
                assert data["processor_type"] == processor_type

            finally:
                file_handlers.UPLOAD_FOLDER = original_folder


class TestParsePreviewMessage:
    """parse_preview_message函数测试"""

    def test_parse_preview_message_complete(self):
        """测试解析完整的预览消息"""
        message = (
            "原有数据：100条, 上传数据：50条, 重复数据：20条, 实际新增：30条, 变更后数据：130条"
        )

        result = file_handlers.parse_preview_message(message)

        assert result is not None
        assert result["original_count"] == 100
        assert result["uploaded_count"] == 50
        assert result["duplicate_count"] == 20
        assert result["new_count"] == 30
        assert result["final_count"] == 130
        assert result["total_count"] == 130

    def test_parse_preview_message_partial(self):
        """测试解析部分信息的消息"""
        message = "上传数据：50条, 实际新增：30条"

        result = file_handlers.parse_preview_message(message)

        assert result is not None
        assert result["uploaded_count"] == 50
        assert result["new_count"] == 30
        assert result["original_count"] == 0
        assert result["duplicate_count"] == 0

    def test_parse_preview_message_with_spaces(self):
        """测试带空格的消息"""
        message = "原有数据：100条, 上传数据：50条"

        result = file_handlers.parse_preview_message(message)

        assert result is not None
        assert result["original_count"] == 100
        assert result["uploaded_count"] == 50

    def test_parse_preview_message_empty(self):
        """测试空消息"""
        result = file_handlers.parse_preview_message("")

        assert result is not None
        assert result["original_count"] == 0
        assert result["uploaded_count"] == 0

    def test_parse_preview_message_no_match(self):
        """测试没有匹配的消息"""
        message = "这是一条不包含任何统计信息的消息"

        result = file_handlers.parse_preview_message(message)

        assert result is not None
        assert all(value == 0 for value in result.values())

    def test_parse_preview_message_zero_values(self):
        """测试包含0值的消息"""
        message = "原有数据：0条, 上传数据：0条, 实际新增：0条"

        result = file_handlers.parse_preview_message(message)

        assert result is not None
        assert result["original_count"] == 0
        assert result["uploaded_count"] == 0
        assert result["new_count"] == 0


class TestCleanupTempFiles:
    """cleanup_temp_files函数测试"""

    def test_cleanup_temp_files_success(self):
        """测试成功清理临时文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                temp_id = "test_id_123"

                # 创建一些临时文件
                files_to_create = [
                    f"{temp_id}_file.xlsx",
                    f"{temp_id}_info.json",
                    f"{temp_id}_other.txt",
                ]

                for filename in files_to_create:
                    filepath = os.path.join(tmpdir, filename)
                    with open(filepath, "w") as f:
                        f.write("test")

                # 验证文件存在
                for filename in files_to_create:
                    assert os.path.exists(os.path.join(tmpdir, filename))

                # 清理文件
                file_handlers.cleanup_temp_files(temp_id)

                # 验证文件被删除
                for filename in files_to_create:
                    assert not os.path.exists(os.path.join(tmpdir, filename))

            finally:
                file_handlers.UPLOAD_FOLDER = original_folder

    def test_cleanup_temp_files_partial_match(self):
        """测试清理时只删除匹配的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                temp_id = "test_id_123"

                # 创建匹配和不匹配的文件
                matching_files = [f"{temp_id}_file1.xlsx", f"{temp_id}_file2.json"]
                other_files = ["other_id_file.xlsx", "unrelated.txt"]

                for filename in matching_files + other_files:
                    filepath = os.path.join(tmpdir, filename)
                    with open(filepath, "w") as f:
                        f.write("test")

                # 清理文件
                file_handlers.cleanup_temp_files(temp_id)

                # 验证匹配的文件被删除
                for filename in matching_files:
                    assert not os.path.exists(os.path.join(tmpdir, filename))

                # 验证不匹配的文件保留
                for filename in other_files:
                    assert os.path.exists(os.path.join(tmpdir, filename))

            finally:
                file_handlers.UPLOAD_FOLDER = original_folder

    def test_cleanup_temp_files_no_files(self):
        """测试清理不存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = file_handlers.UPLOAD_FOLDER
            file_handlers.UPLOAD_FOLDER = tmpdir

            try:
                # 不应该抛出异常
                file_handlers.cleanup_temp_files("nonexistent_id")
            finally:
                file_handlers.UPLOAD_FOLDER = original_folder
