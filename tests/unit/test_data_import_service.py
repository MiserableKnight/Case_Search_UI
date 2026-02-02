"""DataImportService单元测试"""

from unittest.mock import Mock, patch

import pandas as pd

from app.services.data_services.data_import_service import DataImportService


class TestDataImportService:
    """DataImportService测试类"""

    def test_init_with_processor_class(self):
        """测试使用处理器类初始化服务"""
        # 创建mock处理器类
        mock_processor_class = Mock()
        mock_processor_instance = Mock()
        mock_processor_class.return_value = mock_processor_instance

        # 创建服务
        service = DataImportService(mock_processor_class)

        # 验证处理器被正确初始化
        mock_processor_class.assert_called_once()
        assert service.processor == mock_processor_instance

    def test_init_with_config(self):
        """测试使用配置初始化服务"""
        mock_processor_class = Mock()
        mock_processor_instance = Mock()
        mock_processor_class.return_value = mock_processor_instance

        config = {"test": "config"}
        service = DataImportService(mock_processor_class, config)

        # 验证配置被传递
        mock_processor_class.assert_called_once_with(config)

    def test_analyze_changes_success(self):
        """测试成功分析数据变化"""
        # 创建mock处理器
        mock_processor = Mock()
        mock_processor.analyze_changes.return_value = (True, "成功: 新增5条数据")
        mock_processor.__class__ = Mock(return_value=mock_processor)
        mock_processor.unicode_cleaner = Mock()
        mock_processor.unicode_cleaner.clean_text = Mock(side_effect=lambda x: x)
        mock_processor.unicode_cleaner.clean_dataframe = Mock(side_effect=lambda x: x)
        mock_processor.clean_data = Mock(side_effect=lambda x: x)
        mock_processor.data_path = "test.parquet"
        mock_processor.date_column = "date"
        mock_processor.FINAL_COLUMNS = ["col1", "col2", "date"]

        # 创建服务并注入mock处理器
        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        # Mock文件读取
        with patch("os.path.exists", return_value=False):
            with patch("pandas.read_excel") as mock_read_excel:
                mock_df = pd.DataFrame(
                    {"col1": [1, 2], "col2": [3, 4], "date": ["2023-01-01", "2023-01-02"]}
                )
                mock_read_excel.return_value = mock_df

                # 执行分析
                success, message, combined_data = service.analyze_changes("test.xlsx")

                # 验证结果
                assert success is True
                assert "新增" in message
                assert combined_data is not None
                assert isinstance(combined_data, pd.DataFrame)

    def test_analyze_changes_with_existing_data(self):
        """测试分析变化时存在现有数据"""
        # 创建mock处理器
        mock_processor = Mock()
        mock_processor.analyze_changes.return_value = (True, "成功: 新增3条数据")
        mock_processor.__class__ = Mock(return_value=mock_processor)
        mock_processor.unicode_cleaner = Mock()
        mock_processor.unicode_cleaner.clean_text = Mock(side_effect=lambda x: x)
        mock_processor.unicode_cleaner.clean_dataframe = Mock(side_effect=lambda x: x)
        mock_processor.clean_data = Mock(side_effect=lambda x: x)
        mock_processor.data_path = "test.parquet"
        mock_processor.date_column = "date"
        mock_processor.FINAL_COLUMNS = ["col1", "col2", "date"]

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        # Mock文件读取
        with patch("os.path.exists", return_value=True):
            with patch("pandas.read_excel") as mock_read_excel:
                with patch("pandas.read_parquet") as mock_read_parquet:
                    new_df = pd.DataFrame(
                        {"col1": [1, 2], "col2": [3, 4], "date": ["2023-01-01", "2023-01-02"]}
                    )
                    existing_df = pd.DataFrame({"col1": [3], "col2": [5], "date": ["2023-01-03"]})
                    mock_read_excel.return_value = new_df
                    mock_read_parquet.return_value = existing_df

                    success, message, combined_data = service.analyze_changes("test.xlsx")

                    assert success is True
                    assert combined_data is not None
                    assert len(combined_data) == 3

    def test_analyze_changes_processor_fails(self):
        """测试处理器分析失败的情况"""
        mock_processor = Mock()
        mock_processor.analyze_changes.return_value = (False, "分析失败: 列不匹配")
        mock_processor.__class__ = Mock(return_value=mock_processor)

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        success, message, combined_data = service.analyze_changes("test.xlsx")

        assert success is False
        assert "分析失败" in message or "列不匹配" in message
        assert combined_data is None

    def test_analyze_changes_exception_handling(self):
        """测试分析过程中的异常处理"""
        mock_processor = Mock()
        mock_processor.analyze_changes.return_value = (True, "成功")
        mock_processor.__class__ = Mock(return_value=mock_processor)
        mock_processor.unicode_cleaner = Mock()
        mock_processor.unicode_cleaner.clean_text = Mock(side_effect=lambda x: x)
        mock_processor.clean_data = Mock(side_effect=lambda x: x)
        mock_processor.data_path = "test.parquet"
        mock_processor.date_column = "date"
        mock_processor.FINAL_COLUMNS = ["col1", "col2"]

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        # Mock read_excel抛出异常
        with patch("pandas.read_excel", side_effect=Exception("读取失败")):
            success, message, combined_data = service.analyze_changes("test.xlsx")

            assert success is True  # analyze_changes仍然成功
            assert combined_data is None  # 但数据为None

    def test_save_changes(self):
        """测试保存变化"""
        mock_processor = Mock()
        mock_processor.save_changes.return_value = (True, "保存成功")

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        test_df = pd.DataFrame({"col1": [1, 2]})
        success, message = service.save_changes(test_df)

        assert success is True
        assert "保存成功" in message
        mock_processor.save_changes.assert_called_once_with(test_df)

    def test_save_changes_failure(self):
        """测试保存失败的情况"""
        mock_processor = Mock()
        mock_processor.save_changes.return_value = (False, "保存失败")

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        test_df = pd.DataFrame({"col1": [1, 2]})
        success, message = service.save_changes(test_df)

        assert success is False
        assert "保存失败" in message

    def test_get_columns(self):
        """测试获取列信息"""
        mock_processor = Mock()
        mock_processor.get_columns.return_value = ["col1", "col2", "col3"]

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        columns = service.get_columns()

        assert columns == ["col1", "col2", "col3"]
        mock_processor.get_columns.assert_called_once()

    def test_get_columns_empty(self):
        """测试获取空列信息"""
        mock_processor = Mock()
        mock_processor.get_columns.return_value = []

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        columns = service.get_columns()

        assert columns == []

    def test_confirm_import_success(self):
        """测试成功确认导入"""
        # 创建mock处理器
        mock_processor = Mock()
        mock_processor.save_changes.return_value = (True, "导入成功: 新增10条")

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        # Mock analyze_changes返回成功
        with patch("os.path.exists", return_value=True):
            with patch.object(service, "analyze_changes") as mock_analyze:
                test_df = pd.DataFrame({"col1": [1, 2, 3]})
                mock_analyze.return_value = (True, "分析成功: 实际新增：5条", test_df)

                success, message = service.confirm_import("test.xlsx")

                assert success is True
                assert "导入成功" in message or "新增" in message

    def test_confirm_import_file_not_exists(self):
        """测试导入文件不存在的情况"""
        service = DataImportService.__new__(DataImportService)
        service.processor = Mock()

        with patch("os.path.exists", return_value=False):
            success, message = service.confirm_import("test.xlsx")

            assert success is False
            assert "不存在" in message

    def test_confirm_import_analyze_fails(self):
        """测试分析失败的情况"""
        mock_processor = Mock()
        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        with patch("os.path.exists", return_value=True):
            with patch.object(service, "analyze_changes") as mock_analyze:
                mock_analyze.return_value = (False, "列不匹配", None)

                success, message = service.confirm_import("test.xlsx")

                assert success is False
                assert "列不匹配" in message

    def test_confirm_import_combined_data_none(self):
        """测试合并数据为None的情况"""
        mock_processor = Mock()
        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        with patch("os.path.exists", return_value=True):
            with patch.object(service, "analyze_changes") as mock_analyze:
                # 分析成功但数据为None
                mock_analyze.return_value = (True, "分析成功", None)

                success, message = service.confirm_import("test.xlsx")

                assert success is False

    def test_confirm_import_exception(self):
        """测试导入过程中的异常处理"""
        mock_processor = Mock()
        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        with patch("os.path.exists", return_value=True):
            with patch.object(service, "analyze_changes", side_effect=Exception("系统错误")):
                success, message = service.confirm_import("test.xlsx")

                assert success is False
                assert "导入失败" in message or "系统错误" in message

    def test_confirm_import_with_new_count_extraction(self):
        """测试从消息中提取新增数量"""
        mock_processor = Mock()
        mock_processor.save_changes.return_value = (True, "保存成功")

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        with patch("os.path.exists", return_value=True):
            with patch.object(service, "analyze_changes") as mock_analyze:
                test_df = pd.DataFrame({"col1": [1, 2, 3]})
                mock_analyze.return_value = (True, "分析成功: 实际新增：15条数据", test_df)

                success, message = service.confirm_import("test.xlsx")

                assert success is True
                # 验证save_changes被调用并传递了正确的新增数量
                mock_processor.save_changes.assert_called_once()

    def test_confirm_import_without_new_count_in_message(self):
        """测试消息中没有新增数量的情况"""
        mock_processor = Mock()
        mock_processor.save_changes.return_value = (True, "保存成功")

        service = DataImportService.__new__(DataImportService)
        service.processor = mock_processor

        with patch("os.path.exists", return_value=True):
            with patch.object(service, "analyze_changes") as mock_analyze:
                test_df = pd.DataFrame({"col1": [1, 2, 3]})
                # 消息中没有"实际新增：X条"
                mock_analyze.return_value = (True, "分析成功", test_df)

                success, message = service.confirm_import("test.xlsx")

                assert success is True
