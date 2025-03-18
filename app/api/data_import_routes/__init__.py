from flask import Blueprint

bp = Blueprint("data_import", __name__, url_prefix="/import")

from . import (
    case_routes,
    engineering_routes,
    faults_routes,
    manual_routes,
    r_and_i_record_routes,
)
from .data_import_routes import BaseDataImportRoutes

# 导入所有路由模块
__all__ = [
    "bp",
    "BaseDataImportRoutes",
    "case_routes",
    "faults_routes",
    "r_and_i_record_routes",
    "engineering_routes",
    "manual_routes",
]
