"""
类型声明模块
为Flask应用动态添加的属性提供类型支持
"""

from collections.abc import Callable

from flask import Flask
from pandas import DataFrame

from app.services import (
    CaseService,
    EngineeringService,
    FaultReportService,
    ManualService,
    RAndIRecordService,
    WordService,
)
from app.services.temp_file_manager import TempFileManager


class CaseFlask(Flask):
    """
    自定义Flask应用类型，包含动态添加的属性
    """

    # 服务管理器
    temp_manager: TempFileManager
    word_manager: WordService

    # 数据服务
    case_service: CaseService
    fault_report_service: FaultReportService
    r_and_i_record_service: RAndIRecordService
    engineering_service: EngineeringService
    manual_service: ManualService

    # 工具函数
    allowed_file: Callable[[str, list[str] | None], bool]
    load_data_source: Callable[[str], DataFrame | None]


__all__ = ["CaseFlask"]
