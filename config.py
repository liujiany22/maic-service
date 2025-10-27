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

# ==================== 数据轮询配置 ====================
POLLING_ENABLED = os.getenv("POLLING_ENABLED", "true").lower() == "true"
POLLING_INTERVAL = float(os.getenv("POLLING_INTERVAL", "0.1"))  # 秒

# ==================== 初始化目录 ====================
def init_directories():
    """确保必要的目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SERVICE_LOG_DIR.mkdir(parents=True, exist_ok=True)

