"""
WSGI入口文件
用于启动Flask应用
"""

import os

from app import create_app

# 通过环境变量获取配置名称
config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config["DEBUG"],
    )
