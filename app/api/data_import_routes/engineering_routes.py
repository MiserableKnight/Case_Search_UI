from flask import current_app, jsonify, request

from app.services import EngineeringService

from . import bp
from .data_import_routes import BaseDataImportRoutes

engineering_routes = BaseDataImportRoutes("engineering", EngineeringService)


@bp.route("/engineering/import", methods=["POST"])
def import_engineering_data():
    """处理工程文件上传并生成预览"""
    return engineering_routes.process_import()


@bp.route("/engineering/confirm", methods=["POST"])
def confirm_engineering_import():
    """确认导入工程文件数据"""
    return engineering_routes.process_confirm()


@bp.route("/engineering/manual_import", methods=["POST"])
def manual_import_engineering_data():
    """处理手动输入的工程文件数据"""
    return engineering_routes.process_manual_import()
