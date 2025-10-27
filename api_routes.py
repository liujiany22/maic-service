"""
API 路由模块

定义所有 HTTP API 端点
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from config import POLLING_ENABLED
from data_poller import DataPoller
from eyelink_manager import EYELINK_AVAILABLE, eyelink_manager
from models import EyeLinkConfig, EyeLinkMarker, EyeLinkStatusResponse

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 全局数据轮询器（由 main.py 注入）
data_poller: Optional[DataPoller] = None


def set_data_poller(poller: DataPoller) -> None:
    """设置数据轮询器实例"""
    global data_poller
    data_poller = poller


# ==================== EyeLink API ====================

@router.get("/eyelink/status", response_model=EyeLinkStatusResponse, tags=["EyeLink"])
async def get_eyelink_status():
    """获取眼动仪连接状态"""
    return eyelink_manager.get_status()


@router.post("/eyelink/connect", tags=["EyeLink"])
async def connect_eyelink(config: Optional[EyeLinkConfig] = None):
    """
    连接到眼动仪
    
    请求体示例：
    ```json
    {
        "host_ip": "100.1.1.1",
        "dummy_mode": false,
        "screen_width": 1920,
        "screen_height": 1080
    }
    ```
    """
    if not EYELINK_AVAILABLE:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": "PyLink library not available",
                "hint": "Install EyeLink Developers Kit from SR Research"
            }
        )
    
    # 使用默认配置或用户提供的配置
    if config is None:
        from config import (
            EYELINK_DUMMY_MODE,
            EYELINK_HOST_IP,
            EYELINK_SCREEN_HEIGHT,
            EYELINK_SCREEN_WIDTH,
        )
        config = EyeLinkConfig(
            host_ip=EYELINK_HOST_IP,
            dummy_mode=EYELINK_DUMMY_MODE,
            screen_width=EYELINK_SCREEN_WIDTH,
            screen_height=EYELINK_SCREEN_HEIGHT
        )
    
    success = eyelink_manager.connect(
        config.host_ip,
        config.dummy_mode,
        config.screen_width,
        config.screen_height
    )
    
    if success:
        return {"ok": True, "message": f"Connected to EyeLink at {config.host_ip}"}
    else:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": eyelink_manager.error_message}
        )


@router.post("/eyelink/disconnect", tags=["EyeLink"])
async def disconnect_eyelink():
    """断开眼动仪连接"""
    eyelink_manager.disconnect()
    return {"ok": True, "message": "Disconnected from EyeLink"}


@router.post("/eyelink/start_recording", tags=["EyeLink"])
async def start_recording(edf_filename: Optional[str] = None):
    """
    开始记录眼动数据
    
    参数：
    - edf_filename: EDF 文件名（可选，默认使用配置中的文件名）
    """
    if not eyelink_manager.get_status().connected:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "EyeLink not connected"}
        )
    
    if edf_filename is None:
        from config import EYELINK_EDF_FILENAME
        edf_filename = EYELINK_EDF_FILENAME
    
    success = eyelink_manager.start_recording(edf_filename)
    if success:
        return {"ok": True, "message": f"Started recording to {edf_filename}"}
    else:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Failed to start recording"}
        )


@router.post("/eyelink/stop_recording", tags=["EyeLink"])
async def stop_recording():
    """停止记录眼动数据"""
    success = eyelink_manager.stop_recording()
    if success:
        return {"ok": True, "message": "Stopped recording"}
    else:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Failed to stop recording"}
        )


@router.post("/eyelink/marker", tags=["EyeLink"])
async def send_marker(marker: EyeLinkMarker):
    """
    发送标记到眼动仪
    
    请求体示例：
    ```json
    {
        "marker_type": "trial_start",
        "message": "Trial 1 started",
        "trial_id": "trial_001",
        "additional_data": {
            "condition": "baseline"
        }
    }
    ```
    """
    if not eyelink_manager.get_status().connected:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "EyeLink not connected"}
        )
    
    success = eyelink_manager.send_marker(marker)
    if success:
        return {"ok": True, "message": f"Marker sent: {marker.message}"}
    else:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Failed to send marker"}
        )


# ==================== 轮询 API ====================

@router.get("/polling/status", tags=["Polling"])
async def get_polling_status():
    """获取轮询器状态"""
    if data_poller is None:
        return {"enabled": False, "running": False, "interval": 0}
    
    return {
        "enabled": POLLING_ENABLED,
        "running": data_poller.running,
        "interval": data_poller.interval
    }


@router.post("/polling/start", tags=["Polling"])
async def start_polling():
    """启动数据轮询"""
    if data_poller is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Poller not initialized"}
        )
    
    data_poller.start()
    return {"ok": True, "message": "Polling started"}


@router.post("/polling/stop", tags=["Polling"])
async def stop_polling():
    """停止数据轮询"""
    if data_poller is None:
        return {"ok": True, "message": "Poller not initialized"}
    
    data_poller.stop()
    return {"ok": True, "message": "Polling stopped"}


@router.post("/polling/data", tags=["Polling"])
async def add_polling_data(data: Dict[str, Any]):
    """
    手动添加数据到轮询队列
    
    用于测试或手动注入数据
    """
    if data_poller is None:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Poller not initialized"}
        )
    
    data_poller.add_data(data)
    return {"ok": True, "message": "Data added to queue"}
