import logging

from app.services import CaseService, EngineeringService, ManualService

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_service_get_columns():
    services = {
        "case": CaseService(),
        "engineering": EngineeringService(),
        "manual": ManualService(),
    }

    for name, service in services.items():
        try:
            logger.info(f"测试 {name} 服务获取列...")
            columns = service.get_columns()
            logger.info(f"{name} 服务获取列结果: {columns}")
        except Exception as e:
            logger.error(f"{name} 服务获取列出错: {str(e)}", exc_info=True)


if __name__ == "__main__":
    test_service_get_columns()
