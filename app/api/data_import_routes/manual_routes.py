from flask import current_app, jsonify, request

from app.services import ManualService

from . import bp
from .data_import_routes import BaseDataImportRoutes

manual_routes = BaseDataImportRoutes("manual", ManualService)


@bp.route("/manual/import", methods=["POST"])
def import_manual_data():
    """处理手册文件上传并生成预览"""
    return manual_routes.process_import()


@bp.route("/manual/confirm", methods=["POST"])
def confirm_manual_import():
    """确认导入手册数据"""
    return manual_routes.process_confirm()


@bp.route("/manual/manual_import", methods=["POST"])
def manual_import_manual_data():
    """处理手动输入的手册数据"""
    return manual_routes.process_manual_import()
