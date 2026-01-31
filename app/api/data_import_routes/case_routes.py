from app.services import CaseService

from . import bp
from .data_import_routes import BaseDataImportRoutes

case_routes = BaseDataImportRoutes("case", CaseService)


@bp.route("/case/import", methods=["POST"])
def import_case_data():
    """处理案例文件上传并生成预览"""
    return case_routes.process_import()


@bp.route("/case/confirm", methods=["POST"])
def confirm_case_import():
    """确认导入案例数据"""
    return case_routes.process_confirm()


@bp.route("/case/manual_import", methods=["POST"])
def manual_import_case_data():
    """处理手动输入的案例数据"""
    return case_routes.process_manual_import()


@bp.route("/case/preview", methods=["POST"])
def preview_case_data():
    """预览手动输入的案例数据"""
    return case_routes.process_preview()
