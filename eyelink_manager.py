"""
EyeLink 眼动仪管理模块

负责与 EyeLink 1000 Plus 眼动仪的所有交互，包括：
- 连接/断开连接
- 开始/停止记录
- 发送标记到 EDF 文件

注意：本模块的实现基于 SR Research PyLink API 文档
某些实现细节可能需要根据实际硬件配置调整
"""

import logging
import threading
import time
from typing import Optional

from models import (
    EyeLinkConfig,
    EyeLinkMarker,
    EyeLinkStatus,
    EyeLinkStatusResponse,
    MarkerType,
)

# 尝试导入 PyLink
try:
    import pylink
    EYELINK_AVAILABLE = True
except ImportError:
    EYELINK_AVAILABLE = False
    pylink = None

logger = logging.getLogger(__name__)


class EyeLinkManager:
    """
    EyeLink 眼动仪管理器
    
    线程安全的单例模式，管理眼动仪的生命周期
    """
    
    def __init__(self):
        self.tracker: Optional[object] = None  # PyLink tracker 对象
        self.status: EyeLinkStatus = EyeLinkStatus.DISCONNECTED
        self.recording: bool = False
        self.edf_file: Optional[str] = None
        self.session_timestamp: Optional[str] = None  # 会话时间戳
        self.error_message: Optional[str] = None
        self._lock = threading.Lock()
        
    def connect(
        self,
        host_ip: str,
        dummy_mode: bool = False,
        screen_width: int = 1920,
        screen_height: int = 1080
    ) -> bool:
        """
        连接到 EyeLink 眼动仪
        
        Args:
            host_ip: 眼动仪主机 IP 地址（默认: 100.1.1.1）
            dummy_mode: 是否使用虚拟模式（无需实际硬件）
            screen_width: 屏幕宽度（像素）
            screen_height: 屏幕高度（像素）
            
        Returns:
            连接成功返回 True，否则返回 False
            
        注意：
            - 实际硬件连接可能需要调整网络配置
            - 虚拟模式用于测试，不记录真实数据
        """
        logger.info("连接 EyeLink...")
        
        # 检查 PyLink 可用性
        if not EYELINK_AVAILABLE:
            self.error_message = "PyLink library not available. Install EyeLink Developers Kit."
            self.status = EyeLinkStatus.ERROR
            logger.error("PyLink 不可用，请安装 EyeLink Developers Kit")
            return False
        
        try:
            with self._lock:
                self.status = EyeLinkStatus.CONNECTING
                
                # 打印连接参数
                logger.info(f"连接参数:")
                logger.info(f"  - 目标 IP: {host_ip}")
                logger.info(f"  - 虚拟模式: {dummy_mode}")
                logger.info(f"  - 屏幕尺寸: {screen_width} x {screen_height}")
                
                # 创建连接
                if dummy_mode:
                    logger.info("使用虚拟模式")
                    self.tracker = pylink.EyeLink(None)
                else:
                    logger.info(f"连接到设备: {host_ip}")
                    self.tracker = pylink.EyeLink(host_ip)
                
                # 配置屏幕坐标
                self.tracker.sendCommand(f"screen_pixel_coords 0 0 {screen_width-1} {screen_height-1}")
                self.tracker.sendMessage(f"DISPLAY_COORDS 0 0 {screen_width-1} {screen_height-1}")
                
                # 配置标准九点校准 (HV9)
                self.tracker.sendCommand("calibration_type = HV9")
                logger.info("校准类型: HV9 (九点校准)")
                
                # 设置校准点自动步进
                self.tracker.sendCommand("enable_automatic_calibration = YES")
                
                # 设置校准目标颜色和大小（可选）
                self.tracker.sendCommand("calibration_area_proportion = 0.88 0.83")
                self.tracker.sendCommand("validation_area_proportion = 0.88 0.83")
                
                self.status = EyeLinkStatus.CONNECTED
                self.error_message = None
                logger.info("EyeLink 连接成功")
                return True
                
        except Exception as e:
            self.error_message = f"Connection failed: {str(e)}"
            self.status = EyeLinkStatus.ERROR
            logger.error(f"连接失败: {self.error_message}")
            return False
    
    def disconnect(self) -> None:
        """
        断开眼动仪连接
        
        自动停止记录并关闭连接
        """
        try:
            with self._lock:
                if self.tracker:
                    if self.recording:
                        self.stop_recording()
                    self.tracker.close()
                    self.tracker = None
                    
                self.status = EyeLinkStatus.DISCONNECTED
                self.recording = False
                self.edf_file = None  # 清空 EDF 文件名
                logger.info("Disconnected from EyeLink")
                
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)
    
    def start_recording(self, enable_screen_recording: bool = True) -> tuple:
        """
        开始记录眼动数据和屏幕录制
        
        Args:
            enable_screen_recording: 是否同时启动屏幕录制
            
        Returns:
            (成功标志, 会话时间戳) - 时间戳用于文件命名
            
        注意：
            - EDF 文件名自动生成时间戳格式（DOS 8.3兼容）
            - 时间戳格式：YYYYMMDD_HHMMSS
            - 录屏和EDF使用相同的时间戳
        """
        from datetime import datetime
        
        # 生成统一的会话时间戳
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # EyeLink EDF文件名限制：最多8个字符（DOS 8.3格式）
        # 使用简短的时间戳：MMDDHHSS（月日时分秒）
        edf_short_name = datetime.now().strftime("%m%d%H%M") + ".edf"
        
        logger.info(f"开始记录: {edf_short_name} (会话:{session_timestamp}, 录屏:{enable_screen_recording})")
        
        if not self.tracker:
            logger.error("未连接")
            return (False, None)
            
        if self.status != EyeLinkStatus.CONNECTED:
            logger.error(f"状态错误: {self.status.value}")
            return (False, None)
            
        try:
            with self._lock:
                # 打开文件
                self.tracker.openDataFile(edf_short_name)
                self.edf_file = edf_short_name
                self.session_timestamp = session_timestamp  # 保存会话时间戳
                
                # 配置记录参数
                commands = [
                    "file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT",
                    "file_sample_data = LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT",
                    "link_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT",
                    "link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT"
                ]
                
                for cmd in commands:
                    self.tracker.sendCommand(cmd)
                
                # 开始记录
                error = self.tracker.startRecording(1, 1, 1, 1)
                if error:
                    logger.error(f"startRecording 错误: {error}")
                    return (False, None)
                
                self.recording = True
                self.status = EyeLinkStatus.RECORDING
                logger.info(f"✓ EyeLink 记录已开始")
                
                # 启动屏幕录制
                if enable_screen_recording:
                    try:
                        from screen_recorder import screen_recorder
                        # 使用会话时间戳作为录屏文件名
                        screen_recorder.start_recording(session_timestamp)
                    except Exception as e:
                        logger.warning(f"屏幕录制启动失败: {e}")
                
                return (True, session_timestamp)
                
        except Exception as e:
            logger.error(f"记录启动失败: {e}")
            return (False, None)
    
    def stop_recording(self, save_local: bool = False, local_dir: str = None) -> bool:
        """
        停止记录并可选保存文件到本地
        
        Args:
            save_local: 是否保存文件到本地
            local_dir: 本地保存目录
            
        Returns:
            成功返回 True
        """
        if not self.tracker or not self.recording:
            return True
            
        try:
            with self._lock:
                logger.info(f"停止记录: {self.edf_file}")
                self.tracker.stopRecording()
                
                # 保存到本地
                saved_edf_path = None
                if save_local and local_dir and self.edf_file and self.session_timestamp:
                    from pathlib import Path
                    
                    save_path = Path(local_dir)
                    save_path.mkdir(parents=True, exist_ok=True)
                    
                    # 使用会话时间戳作为最终文件名
                    local_file = save_path / f"{self.session_timestamp}.edf"
                    
                    try:
                        self.tracker.receiveDataFile(self.edf_file, str(local_file))
                        logger.info(f"✓ EDF已保存: {local_file}")
                        saved_edf_path = local_file  # 保存实际路径
                    except Exception as e:
                        logger.error(f"EDF传输失败: {e}")
                
                self.tracker.closeDataFile()
                self.recording = False
                self.status = EyeLinkStatus.CONNECTED
                logger.info("✓ EyeLink 记录已停止")
                
                # 停止屏幕录制并处理 overlay
                try:
                    from screen_recorder import screen_recorder, overlay_gaze_on_video
                    
                    # 停止录屏
                    video_path = screen_recorder.stop_recording()
                    
                    # 如果有录屏且有 EDF 文件，进行 overlay 处理
                    if video_path and saved_edf_path:
                        logger.info("处理 Overlay...")
                        
                        from pathlib import Path
                        
                        # 使用实际保存的 EDF 文件路径
                        if saved_edf_path.exists():
                            # Overlay视频：使用时间戳_gaze.mp4
                            overlay_output = str(Path(video_path).parent / f"{self.session_timestamp}_gaze.mp4")
                            
                            # 导入配置
                            import config
                            
                            overlay_gaze_on_video(
                                video_path=video_path,
                                edf_path=str(saved_edf_path),
                                output_path=overlay_output,
                                eye=config.EYELINK_OVERLAY_EYE
                            )
                            
                            logger.info(f"✓ 原始录屏: {Path(video_path).name}")
                            logger.info(f"✓ Overlay录屏: {Path(overlay_output).name}")
                        else:
                            logger.warning(f"EDF 文件未找到: {saved_edf_path}")
                    elif video_path:
                        logger.info(f"✓ 录屏已保存 (无 Overlay)")
                
                except Exception as e:
                    logger.error(f"录屏处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                return True
                
        except Exception as e:
            logger.error(f"停止记录失败: {e}")
            return False
    
    def send_marker(self, marker: EyeLinkMarker) -> bool:
        """
        发送标记到眼动仪
        
        Args:
            marker: 标记数据对象
            
        Returns:
            成功返回 True，否则返回 False
            
        注意：
            - 标记会被写入 EDF 文件，可在 Data Viewer 中查看
            - MESSAGE 命令格式需严格遵循 EyeLink 规范
            - TRIAL_VAR 变量会在 Data Viewer 中显示
        """
        # 检查状态
        if not self.tracker:
            logger.warning("❌ 无法发送标记: Tracker 对象不存在")
            return False
            
        if self.status not in [EyeLinkStatus.CONNECTED, EyeLinkStatus.RECORDING]:
            logger.warning(f"❌ 无法发送标记: 状态不正确 ({self.status.value})")
            logger.warning("需要 CONNECTED 或 RECORDING 状态")
            return False
        
        logger.debug("-" * 40)
        logger.debug(f"发送标记: {marker.marker_type.value}")
        logger.debug(f"  消息: {marker.message}")
        if marker.trial_id:
            logger.debug(f"  试验ID: {marker.trial_id}")
        if marker.additional_data:
            logger.debug(f"  附加数据: {marker.additional_data}")
            
        try:
            with self._lock:
                message_to_send = None
                
                # 根据标记类型发送不同格式的消息
                if marker.marker_type == MarkerType.MESSAGE:
                    message_to_send = marker.message
                    
                elif marker.marker_type == MarkerType.TRIAL_START:
                    # TRIALID 是 Data Viewer 识别试验开始的特殊标记
                    trial_id = marker.trial_id or "unknown"
                    message_to_send = f"TRIALID {trial_id}"
                    
                elif marker.marker_type == MarkerType.TRIAL_END:
                    # TRIAL_RESULT 标记试验结束，0 表示成功
                    message_to_send = "TRIAL_RESULT 0"
                    
                elif marker.marker_type == MarkerType.STIMULUS_ON:
                    message_to_send = f"STIMULUS_ON {marker.message}"
                    
                elif marker.marker_type == MarkerType.STIMULUS_OFF:
                    message_to_send = f"STIMULUS_OFF {marker.message}"
                    
                elif marker.marker_type == MarkerType.RESPONSE:
                    message_to_send = f"RESPONSE {marker.message}"
                    
                elif marker.marker_type == MarkerType.CUSTOM:
                    message_to_send = marker.message
                
                # 发送消息
                if message_to_send:
                    self.tracker.sendMessage(message_to_send)
                
                # 发送附加变量
                if marker.additional_data:
                    for key, value in marker.additional_data.items():
                        self.tracker.sendMessage(f"!V TRIAL_VAR {key} {value}")
                
                logger.debug(f"Marker: {message_to_send}")
                return True
                
        except Exception as e:
            logger.error(f"发送标记失败: {e}")
            return False
    
    def do_calibration(self, width: int = 1920, height: int = 1080) -> bool:
        """
        执行校准
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
            
        Returns:
            成功返回 True
        """
        if not self.tracker:
            logger.error("未连接到 EyeLink")
            return False
        
        try:
            from eyelink_graphics import do_tracker_setup
            logger.info("开始校准...")
            success = do_tracker_setup(self.tracker, width, height)
            if success:
                logger.info("✓ 校准完成")
            return success
        except Exception as e:
            logger.error(f"校准失败: {e}")
            return False
    
    def do_validation(self, width: int = 1920, height: int = 1080) -> bool:
        """
        执行验证（与校准使用相同界面，在界面中选择 validate）
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
            
        Returns:
            成功返回 True
        """
        return self.do_calibration(width, height)
    
    def do_drift_correct(self, x: int = None, y: int = None, width: int = 1920, height: int = 1080) -> bool:
        """
        执行漂移校正
        
        Args:
            x: 校正点 x 坐标（默认屏幕中心）
            y: 校正点 y 坐标（默认屏幕中心）
            width: 屏幕宽度
            height: 屏幕高度
            
        Returns:
            成功返回 True
        """
        if not self.tracker:
            logger.error("未连接到 EyeLink")
            return False
        
        try:
            from eyelink_graphics import do_drift_correct
            
            # 默认屏幕中心
            if x is None:
                x = width // 2
            if y is None:
                y = height // 2
            
            logger.info(f"漂移校正: ({x}, {y})")
            success = do_drift_correct(self.tracker, x, y)
            if success:
                logger.info("✓ 漂移校正完成")
            return success
        except Exception as e:
            logger.error(f"漂移校正失败: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """
        发送简单消息到 EyeLink
        
        Args:
            message: 消息内容
            
        Returns:
            成功返回 True
        """
        if not self.tracker:
            return False
        
        try:
            self.tracker.sendMessage(message)
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    def get_status(self) -> EyeLinkStatusResponse:
        """获取当前状态"""
        return EyeLinkStatusResponse(
            status=self.status,
            connected=self.tracker is not None and self.status in [
                EyeLinkStatus.CONNECTED,
                EyeLinkStatus.RECORDING
            ],
            recording=self.recording,
            edf_file=self.edf_file,
            error_message=self.error_message
        )


# 全局单例实例
eyelink_manager = EyeLinkManager()
