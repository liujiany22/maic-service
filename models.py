"""
数据模型定义
使用 Pydantic 进行数据验证
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ==================== 基础数据模型 ====================

class IngressPayload(BaseModel):
    """接收的外部数据载荷"""
    event: Optional[str] = Field(default=None, description="事件名称")
    data: Dict[str, Any] = Field(default_factory=dict, description="数据内容")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="元信息")
    ts: Optional[datetime] = Field(default=None, description="时间戳")
    request_id: Optional[str] = Field(default=None, description="请求ID")


class AckResponse(BaseModel):
    """确认响应"""
    ok: bool
    request_id: str
    received_keys: Dict[str, bool]


# ==================== EyeLink 相关模型 ====================

class EyeLinkStatus(str, Enum):
    """眼动仪状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECORDING = "recording"
    ERROR = "error"


class MarkerType(str, Enum):
    """标记类型枚举"""
    MESSAGE = "message"           # 普通消息
    TRIAL_START = "trial_start"   # 试验开始
    TRIAL_END = "trial_end"       # 试验结束
    STIMULUS_ON = "stimulus_on"   # 刺激呈现
    STIMULUS_OFF = "stimulus_off" # 刺激消失
    RESPONSE = "response"         # 被试反应
    CUSTOM = "custom"             # 自定义标记


class EyeLinkMarker(BaseModel):
    """眼动仪标记数据"""
    marker_type: MarkerType
    message: str
    timestamp: Optional[datetime] = None
    trial_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class EyeLinkStatusResponse(BaseModel):
    """眼动仪状态响应"""
    status: EyeLinkStatus
    connected: bool
    recording: bool
    edf_file: Optional[str] = None
    error_message: Optional[str] = None


class EyeLinkConfig(BaseModel):
    """眼动仪配置"""
    host_ip: str
    dummy_mode: bool = False
    screen_width: int = 1920
    screen_height: int = 1080
    edf_filename: str = "experiment.edf"

