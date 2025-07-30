from flask import current_app, jsonify, request

from app.services import RAndIRecordService

from . import bp
from .data_import_routes import BaseDataImportRoutes

r_and_i_record_routes = BaseDataImportRoutes(
    "r_and_i_record", RAndIRecordService, file_prefix="部件拆换记录"
)


@bp.route("/r_and_i_record/import", methods=["POST"])
def import_r_and_i_record_data():
    """处理部件拆换记录文件上传并生成预览"""
    return r_and_i_record_routes.process_import()


@bp.route("/r_and_i_record/confirm", methods=["POST"])
def confirm_r_and_i_record_import():
    """确认导入部件拆换记录数据"""
    response = r_and_i_record_routes.process_confirm()

    # 额外清除故障报告数据缓存
    if response.status_code == 200:
        from app import data_frames

        if "faults" in data_frames:
            del data_frames["faults"]

    return response


@bp.route("/r_and_i_record/manual_import", methods=["POST"])
def manual_import_r_and_i_record_data():
    """处理手动输入的部件拆换记录数据"""
    return r_and_i_record_routes.process_manual_import()


@bp.route("/r_and_i_record/preview", methods=["POST"])
def preview_r_and_i_record_data():
    """预览手动输入的部件拆换记录数据"""
    return r_and_i_record_routes.process_preview()
