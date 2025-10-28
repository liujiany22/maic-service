"""
MAIC JSON Service - 主服务文件

一个集成了 EyeLink 1000 Plus 眼动仪的 FastAPI 服务
支持实时数据接收和标记功能
消息频率由 MAIC 服务器控制，通过 /ingest 端点接收
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

import config
from eyelink_manager import EYELINK_AVAILABLE, eyelink_manager
from models import AckResponse, EyeLinkMarker, IngressPayload, MarkerType
from utils import generate_event_brief
from custom_control import initialize_custom_control, handle_control_message

# 初始化日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 初始化必要的目录
config.init_directories()


# ==================== 自定义控制区域 ====================
# 
# 这个区域供用户自定义 EyeLink 控制逻辑
# 你可以在这里编写代码来响应特定的输入或事件
# 

def custom_eyelink_control():
    """
    自定义 EyeLink 控制函数
    
    这个函数会在服务启动时被调用。
    实际的自定义逻辑请在 custom_control.py 文件中编写。
    
    custom_control.py 提供了：
    1. 键盘控制示例
    2. 消息处理示例
    3. 定时任务示例
    4. 便捷的工具函数
    
    直接编辑 custom_control.py 来添加你的自定义逻辑。
    """
    initialize_custom_control()


# ==================== 生命周期事件 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION} on port {config.PORT}")
    
    # 打印配置信息（便于调试）
    config.print_config()
    
    # 检查 EyeLink 可用性
    if not EYELINK_AVAILABLE:
        logger.warning("⚠️  PyLink 不可用 - EyeLink 功能已禁用")
        logger.warning("如需使用眼动仪，请安装 EyeLink Developers Kit")
    else:
        logger.info("✓ PyLink 可用 - EyeLink 功能已启用")
        
        # 自动连接 EyeLink
        if config.EYELINK_AUTO_CONNECT:
            logger.info("正在自动连接 EyeLink...")
            success = eyelink_manager.connect(
                host_ip=config.EYELINK_HOST_IP,
                dummy_mode=config.EYELINK_DUMMY_MODE,
                screen_width=config.EYELINK_SCREEN_WIDTH,
                screen_height=config.EYELINK_SCREEN_HEIGHT
            )
            
            if success:
                logger.info("✅ EyeLink 连接成功")
                logger.info("💡 使用自定义控制来管理实验流程")
            else:
                logger.error("❌ EyeLink 连接失败")
                logger.error("服务将继续运行，但 EyeLink 功能不可用")
        else:
            logger.info("自动连接已禁用")
    
    # 调用自定义控制函数
    logger.info("启动自定义控制...")
    custom_eyelink_control()
    
    yield
    
    # 关闭
    logger.info(f"Shutting down {config.APP_NAME}")
    
    # 停止记录并断开眼动仪
    try:
        status = eyelink_manager.get_status()
        
        if status.recording:
            logger.info("停止 EyeLink 记录...")
            eyelink_manager.stop_recording()
        
        if status.connected:
            logger.info("断开 EyeLink 连接...")
            eyelink_manager.disconnect()
            
        logger.info("✓ EyeLink 清理完成")
    except Exception as e:
        logger.error(f"EyeLink 清理时出错: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="集成 EyeLink 眼动仪的数据收集服务",
    lifespan=lifespan
)


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
        logger.warning("EyeLink not connected, skipping marker")
        return
    
    try:
        event = payload.get("event", "")
        data = payload.get("data", {})
        
        # ============================================================
        # 自定义特殊事件处理区域
        # 尝试使用 custom_control.py 中的处理函数
        # ============================================================
        
        if handle_control_message(event, data):
            # 消息已被自定义处理函数处理，不再发送标准标记
            logger.debug(f"Event {event} handled by custom control")
            return
        
        # ============================================================
        # 标准标记发送
        # ============================================================
        
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
