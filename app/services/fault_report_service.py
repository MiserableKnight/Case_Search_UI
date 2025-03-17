"""
故障报告处理服务，提供对故障报告数据的处理功能
"""
from app.core.fault_report_processor import FaultReportProcessor

class FaultReportService:
    """故障报告处理服务类，封装对FaultReportProcessor的调用"""
    
    def __init__(self, config=None):
        """
        初始化故障报告处理服务
        
        Args:
            config: 配置信息，默认为None，使用默认配置
        """
        self.processor = FaultReportProcessor(config)
    
    def process_fault_report_file(self, file_path, file_type=None):
        """
        处理故障报告文件
        
        Args:
            file_path: 文件路径
            file_type: 文件类型，默认为None，自动识别
            
        Returns:
            处理结果
        """
        # 这里可以添加特定于故障报告的处理逻辑
        return {"status": "success", "message": "故障报告文件处理成功"}
    
    def analyze_changes(self, temp_path):
        """
        分析数据变化
        
        Args:
            temp_path: 临时文件路径
            
        Returns:
            (success, message, combined_data): 分析结果
        """
        # 创建一个新的FaultReportProcessor实例，传入临时文件路径
        temp_processor = FaultReportProcessor(temp_path)
        return temp_processor.analyze_changes()
        
    def save_changes(self, combined_data):
        """
        保存数据变化
        
        Args:
            combined_data: 合并后的数据
            
        Returns:
            (success, message): 保存结果
        """
        return self.processor.save_changes(combined_data)
    
    def get_columns(self):
        """
        获取故障报告数据的列信息
        
        Returns:
            列信息列表
        """
        return self.processor.get_columns() 