"""
默认配置文件
包含应用的基本配置项
"""

import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DefaultConfig:
    """默认配置类"""

    # Flask配置
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev_key_for_session")
    DEBUG = False
    TESTING = False

    # 数据目录配置
    DATA_CONFIG = {
        "data_dir": os.path.join(BASE_DIR, "data"),
        "temp_dir": os.path.join(BASE_DIR, "data", "temp"),
        "processed_dir": os.path.join(BASE_DIR, "data", "processed"),
        "raw_dir": os.path.join(BASE_DIR, "data", "raw"),
    }

    # 文件配置
    UPLOAD_FOLDER = DATA_CONFIG["temp_dir"]
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    SENSITIVE_WORDS_FILE = os.path.join(DATA_CONFIG["raw_dir"], "sensitive_words.json")

    # 文件配置字典（用于兼容）
    FILE_CONFIG = {
        "UPLOAD_FOLDER": UPLOAD_FOLDER,
        "SENSITIVE_WORDS_FILE": SENSITIVE_WORDS_FILE,
    }

    # 数据源配置
    DATA_SOURCES = {
        "case": os.path.join("raw", "case.parquet"),
        "engineering": os.path.join("raw", "engineering.parquet"),
        "manual": os.path.join("raw", "manual.parquet"),
        "faults": os.path.join("raw", "faults.parquet"),
        "r_and_i_record": os.path.join("raw", "r_and_i_record.parquet"),
    }

    # 允许的文件类型
    ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv", "parquet"}

    # 安全配置
    CONTENT_SECURITY_POLICY = (
        "default-src 'self' lib.baomitu.com; "
        "style-src 'self' 'unsafe-inline' lib.baomitu.com; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' lib.baomitu.com; "
        "img-src 'self' data:; "
        "font-src 'self' data: lib.baomitu.com;"
    )
