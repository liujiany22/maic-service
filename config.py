"""
配置管理模块
统一管理所有配置项，支持环境变量和 .env 文件
"""

import os
from pathlib import Path

# 加载 .env 文件
def load_env_file():
    """加载 .env 文件到环境变量"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ[key] = value

load_env_file()

# ==================== 基础配置 ====================
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logdata"
SERVICE_LOG_DIR = BASE_DIR / "log"
RECORDING_DIR = LOG_DIR / "recordings"  # 录屏文件目录

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

# 启动时自动连接 EyeLink
EYELINK_AUTO_CONNECT = os.getenv("EYELINK_AUTO_CONNECT", "true").lower() == "true"

# Overlay 使用的眼睛（"left" 或 "right"，默认 "right"）
EYELINK_OVERLAY_EYE = os.getenv("EYELINK_OVERLAY_EYE", "right").lower()

# ==================== 初始化目录 ====================
def init_directories():
    """确保必要的目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SERVICE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    RECORDING_DIR.mkdir(parents=True, exist_ok=True)


def print_config():
    """打印当前配置"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"{APP_NAME} v{APP_VERSION} Port:{PORT}")

