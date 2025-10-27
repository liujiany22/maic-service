"""
配置管理模块
统一管理所有配置项，支持环境变量覆盖
"""

import os
from pathlib import Path

# ==================== 基础配置 ====================
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logdata"
SERVICE_LOG_DIR = BASE_DIR / "log"

APP_NAME = "MAIC JSON Service"
APP_VERSION = "1.0.0"
PORT = int(os.getenv("MAIC_PORT", "8123"))

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s | %(message)s"

# ==================== EyeLink 配置 ====================
# 注意：这些配置涉及 EyeLink 1000 Plus 眼动仪硬件
# 如果不确定，请保持默认值或咨询 SR Research 技术支持
EYELINK_HOST_IP = os.getenv("EYELINK_HOST_IP", "100.1.1.1")  # 眼动仪主机 IP（默认值）
EYELINK_DUMMY_MODE = os.getenv("EYELINK_DUMMY_MODE", "false").lower() == "true"
EYELINK_SCREEN_WIDTH = int(os.getenv("EYELINK_SCREEN_WIDTH", "1920"))
EYELINK_SCREEN_HEIGHT = int(os.getenv("EYELINK_SCREEN_HEIGHT", "1080"))
EYELINK_EDF_FILENAME = os.getenv("EYELINK_EDF_FILENAME", "experiment.edf")

# 启动时自动连接 EyeLink
EYELINK_AUTO_CONNECT = os.getenv("EYELINK_AUTO_CONNECT", "true").lower() == "true"
# 启动时自动开始记录
EYELINK_AUTO_RECORD = os.getenv("EYELINK_AUTO_RECORD", "true").lower() == "true"

# ==================== 初始化目录 ====================
def init_directories():
    """确保必要的目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SERVICE_LOG_DIR.mkdir(parents=True, exist_ok=True)


def print_config():
    """打印当前配置（用于调试）"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("当前配置:")
    logger.info("=" * 60)
    logger.info(f"应用名称: {APP_NAME}")
    logger.info(f"版本: {APP_VERSION}")
    logger.info(f"端口: {PORT}")
    logger.info(f"日志级别: {LOG_LEVEL}")
    logger.info("")
    logger.info("EyeLink 配置:")
    logger.info(f"  主机 IP: {EYELINK_HOST_IP}")
    logger.info(f"  虚拟模式: {EYELINK_DUMMY_MODE}")
    logger.info(f"  屏幕尺寸: {EYELINK_SCREEN_WIDTH} x {EYELINK_SCREEN_HEIGHT}")
    logger.info(f"  EDF 文件: {EYELINK_EDF_FILENAME}")
    logger.info(f"  自动连接: {EYELINK_AUTO_CONNECT}")
    logger.info(f"  自动记录: {EYELINK_AUTO_RECORD}")
    logger.info("")
    logger.info("目录:")
    logger.info(f"  数据目录: {LOG_DIR}")
    logger.info(f"  日志目录: {SERVICE_LOG_DIR}")
    logger.info("=" * 60)

