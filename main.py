"""
MAIC JSON Service - 主服务文件

一个集成了 EyeLink 1000 Plus 眼动仪的 FastAPI 服务
支持实时数据标记和轮询机制
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

import api_routes
import config
from data_poller import DataPoller
from eyelink_manager import EYELINK_AVAILABLE, eyelink_manager
from models import AckResponse, EyeLinkMarker, IngressPayload, MarkerType
from utils import generate_event_brief

# 初始化日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 初始化必要的目录
config.init_directories()

# 创建 FastAPI 应用
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="集成 EyeLink 眼动仪的数据收集服务"
)

# 初始化数据轮询器
data_poller = DataPoller(config.POLLING_INTERVAL)
api_routes.set_data_poller(data_poller)

# 注册路由
app.include_router(api_routes.router)


# ==================== 生命周期事件 ====================

@app.on_event("startup")
async def on_startup():
    """应用启动时的初始化"""
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION} on port {config.PORT}")
    logger.info(f"EyeLink available: {EYELINK_AVAILABLE}")
    
    # 启动数据轮询器
    if config.POLLING_ENABLED:
        data_poller.start()
        logger.info("Data polling enabled")


@app.on_event("shutdown")
async def on_shutdown():
    """应用关闭时的清理"""
    logger.info(f"Shutting down {config.APP_NAME}")
    
    # 停止轮询
    if config.POLLING_ENABLED:
        data_poller.stop()
    
    # 断开眼动仪
    if eyelink_manager.get_status().connected:
        eyelink_manager.disconnect()


# ==================== 核心API ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": config.APP_NAME,
        "version": config.APP_VERSION,
        "eyelink_available": EYELINK_AVAILABLE
    }


@app.post("/ingest", response_model=AckResponse)
async def ingest_data(request: Request, background_tasks: BackgroundTasks):
    """
    接收外部数据并处理
    
    功能：
    1. 验证并解析 JSON 数据
    2. 生成唯一的 request_id
    3. 异步保存到日志文件
    4. 自动发送标记到眼动仪（如果已连接）
    """
    try:
        # 解析 JSON
        raw_data = await request.json()
        if not isinstance(raw_data, dict):
            raise HTTPException(
                status_code=400,
                detail="JSON must be an object (dict)"
            )
        
        # 验证数据
        try:
            parsed = IngressPayload(**raw_data)
        except ValidationError as ve:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "ValidationError",
                    "detail": json.loads(ve.json())
                }
            )
        
        # 生成 request_id
        request_id = parsed.request_id or uuid.uuid4().hex
        payload_dict = raw_data.copy()
        payload_dict["request_id"] = request_id
        
        # 后台处理
        background_tasks.add_task(process_data, payload_dict, request_id)
        
        # 返回确认
        return AckResponse(
            ok=True,
            request_id=request_id,
            received_keys={k: True for k in raw_data.keys()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in ingest: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "ServerError"}
        )


# ==================== 数据处理 ====================

async def process_data(payload: Dict[str, Any], request_id: str) -> None:
    """
    处理接收到的数据
    
    功能：
    1. 保存到日志文件
    2. 发送标记到眼动仪
    """
    try:
        # 生成时间戳和文件名
        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y%m%d-%H%M%S")
        filename = f"{ts_str}_{request_id}.txt"
        filepath = config.LOG_DIR / filename
        
        # 生成事件简报
        event_brief = generate_event_brief(request_id, payload)
        
        # 准备写入的数据
        log_data = {
            "request_id": request_id,
            "received_at": now.isoformat(),
            "event_brief": event_brief,
            "payload": payload
        }
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Processed: {request_id} -> {filepath}")
        
        # 发送标记到眼动仪
        await send_eyelink_marker(payload, request_id, now)
        
    except Exception as e:
        logger.exception(f"Error processing data: {e}")


async def send_eyelink_marker(
    payload: Dict[str, Any],
    request_id: str,
    timestamp: datetime
) -> None:
    """
    根据接收到的数据自动发送眼动仪标记
    """
    if not eyelink_manager.get_status().connected:
        return
    
    try:
        event = payload.get("event", "")
        data = payload.get("data", {})
        
        # 创建标记
        marker = EyeLinkMarker(
            marker_type=MarkerType.MESSAGE,
            message=f"EVENT {event}",
            timestamp=timestamp,
            trial_id=data.get("trial_id"),
            additional_data={
                "request_id": request_id,
                "event": event
            }
        )
        
        # 发送标记
        success = eyelink_manager.send_marker(marker)
        if success:
            logger.debug(f"Sent EyeLink marker for event: {event}")
        else:
            logger.warning(f"Failed to send EyeLink marker: {event}")
            
    except Exception as e:
        logger.error(f"Error sending EyeLink marker: {e}")


# ==================== 程序入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=False
    )
