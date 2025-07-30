"""
案例处理服务，提供对案例数据的处理功能
"""

from app.core.data_processors.case_processor import CaseProcessor

from .data_import_service import DataImportService


class CaseService(DataImportService):
    """案例处理服务类，封装对CaseProcessor的调用"""

    def __init__(self, config=None):
        """
        初始化案例处理服务

        Args:
            config: 配置信息，默认为None，使用默认配置
        """
        super().__init__(CaseProcessor, config)

    def process_case_file(self, file_path, file_type=None):
        """
        处理案例文件

        Args:
            file_path: 文件路径
            file_type: 文件类型，默认为None，自动识别

        Returns:
            处理结果
        """
        return self.processor.process_file(file_path, file_type)

    def process_case_text(self, text, case_info=None):
        """
        处理案例文本

        Args:
            text: 案例文本
            case_info: 案例信息，默认为None

        Returns:
            处理结果
        """
        return self.processor.process_text(text, case_info)

    def extract_case_info(self, text):
        """
        提取案例信息

        Args:
            text: 案例文本

        Returns:
            案例信息
        """
        return self.processor.extract_case_info(text)

    def save_case(self, case_data):
        """
        保存案例

        Args:
            case_data: 案例数据

        Returns:
            保存结果
        """
        return self.processor.save_case(case_data)

    def get_case_by_id(self, case_id):
        """
        根据ID获取案例

        Args:
            case_id: 案例ID

        Returns:
            案例数据
        """
        return self.processor.get_case_by_id(case_id)
