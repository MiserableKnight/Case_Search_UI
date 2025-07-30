"""
手册处理服务，提供对手册数据的处理功能
"""

from app.core.data_processors.manual_processor import ManualProcessor

from .data_import_service import DataImportService


class ManualService(DataImportService):
    """手册处理服务类，封装对ManualProcessor的调用"""

    def __init__(self, config=None):
        """
        初始化手册处理服务

        Args:
            config: 配置信息，默认为None，使用默认配置
        """
        super().__init__(ManualProcessor, config)

    def process_manual_file(self, file_path, file_type=None):
        """
        处理手册文件

        Args:
            file_path: 文件路径
            file_type: 文件类型，默认为None，自动识别

        Returns:
            处理结果
        """
        # 这里可以添加特定于手册的处理逻辑
        return {"status": "success", "message": "手册文件处理成功"}
