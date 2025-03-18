from flask import current_app, jsonify, request

from app.services import FaultReportService

from . import bp
from .data_import_routes import BaseDataImportRoutes

faults_routes = BaseDataImportRoutes(
    "faults", FaultReportService, file_prefix="故障报告"
)


@bp.route("/faults/import", methods=["POST"])
def import_faults_data():
    """处理故障报告文件上传并生成预览"""
    return faults_routes.process_import()


@bp.route("/faults/confirm", methods=["POST"])
def confirm_faults_import():
    """确认导入故障报告数据"""
    return faults_routes.process_confirm()


@bp.route("/faults/manual_import", methods=["POST"])
def manual_import_faults_data():
    """处理手动输入的故障报告数据"""
    return faults_routes.process_manual_import()
