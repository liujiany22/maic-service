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
        if not EYELINK_AVAILABLE:
            self.error_message = "PyLink library not available. Install EyeLink Developers Kit."
            self.status = EyeLinkStatus.ERROR
            logger.error(self.error_message)
            return False
            
        try:
            with self._lock:
                self.status = EyeLinkStatus.CONNECTING
                logger.info(f"Connecting to EyeLink at {host_ip} (dummy={dummy_mode})")
                
                # 创建连接
                if dummy_mode:
                    self.tracker = pylink.EyeLink(None)
                    logger.warning("Running in DUMMY mode - no real hardware connection")
                else:
                    self.tracker = pylink.EyeLink(host_ip)
                    
                # 配置屏幕坐标
                # 注意：这些命令直接发送给眼动仪，格式必须严格遵循 EyeLink 规范
                self.tracker.sendCommand(
                    f"screen_pixel_coords 0 0 {screen_width-1} {screen_height-1}"
                )
                self.tracker.sendMessage(
                    f"DISPLAY_COORDS 0 0 {screen_width-1} {screen_height-1}"
                )
                
                self.status = EyeLinkStatus.CONNECTED
                self.error_message = None
                logger.info("Successfully connected to EyeLink")
                return True
                
        except Exception as e:
            self.error_message = f"Connection failed: {str(e)}"
            self.status = EyeLinkStatus.ERROR
            logger.error(self.error_message, exc_info=True)
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
                logger.info("Disconnected from EyeLink")
                
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)
    
    def start_recording(self, edf_filename: str = "experiment.edf") -> bool:
        """
        开始记录眼动数据
        
        Args:
            edf_filename: EDF 数据文件名（最多 8 个字符，不含扩展名）
            
        Returns:
            成功返回 True，否则返回 False
            
        注意：
            - EDF 文件名必须符合 DOS 8.3 格式（最多 8 个字符 + .edf）
            - 文件保存在眼动仪主机上，需要手动传输到本地
            - recording 参数 (1,1,1,1) 含义请参考 PyLink 文档
        """
        if not self.tracker or self.status != EyeLinkStatus.CONNECTED:
            logger.error("Cannot start recording - tracker not connected")
            return False
            
        try:
            with self._lock:
                # 打开 EDF 文件
                self.tracker.openDataFile(edf_filename)
                self.edf_file = edf_filename
                
                # 配置记录参数
                # 注意：这些参数控制哪些数据被记录，根据实验需求可能需要调整
                self.tracker.sendCommand(
                    "file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT"
                )
                self.tracker.sendCommand(
                    "file_sample_data = LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT"
                )
                self.tracker.sendCommand(
                    "link_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT"
                )
                self.tracker.sendCommand(
                    "link_sample_data = LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT"
                )
                
                # 开始记录
                # 参数 (1,1,1,1) 表示：record to file, record link events, record link samples, record button events
                error = self.tracker.startRecording(1, 1, 1, 1)
                if error:
                    logger.error(f"startRecording returned error code: {error}")
                    return False
                    
                self.recording = True
                self.status = EyeLinkStatus.RECORDING
                logger.info(f"Started recording to EDF: {edf_filename}")
                return True
                
        except Exception as e:
            logger.error(f"Error starting recording: {e}", exc_info=True)
            return False
    
    def stop_recording(self) -> bool:
        """
        停止记录眼动数据
        
        Returns:
            成功返回 True
        """
        if not self.tracker or not self.recording:
            return True
            
        try:
            with self._lock:
                self.tracker.stopRecording()
                self.tracker.closeDataFile()
                self.recording = False
                self.status = EyeLinkStatus.CONNECTED
                logger.info("Stopped recording")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}", exc_info=True)
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
        if not self.tracker or self.status not in [
            EyeLinkStatus.CONNECTED,
            EyeLinkStatus.RECORDING
        ]:
            logger.warning("Cannot send marker - tracker not ready")
            return False
            
        try:
            with self._lock:
                # 根据标记类型发送不同格式的消息
                if marker.marker_type == MarkerType.MESSAGE:
                    self.tracker.sendMessage(marker.message)
                    
                elif marker.marker_type == MarkerType.TRIAL_START:
                    # TRIALID 是 Data Viewer 识别试验开始的特殊标记
                    trial_id = marker.trial_id or "unknown"
                    self.tracker.sendMessage(f"TRIALID {trial_id}")
                    
                elif marker.marker_type == MarkerType.TRIAL_END:
                    # TRIAL_RESULT 标记试验结束，0 表示成功
                    self.tracker.sendMessage("TRIAL_RESULT 0")
                    
                elif marker.marker_type == MarkerType.STIMULUS_ON:
                    self.tracker.sendMessage(f"STIMULUS_ON {marker.message}")
                    
                elif marker.marker_type == MarkerType.STIMULUS_OFF:
                    self.tracker.sendMessage(f"STIMULUS_OFF {marker.message}")
                    
                elif marker.marker_type == MarkerType.RESPONSE:
                    self.tracker.sendMessage(f"RESPONSE {marker.message}")
                    
                elif marker.marker_type == MarkerType.CUSTOM:
                    self.tracker.sendMessage(marker.message)
                
                # 记录额外的试验变量
                # 格式：!V TRIAL_VAR variable_name value
                if marker.additional_data:
                    for key, value in marker.additional_data.items():
                        self.tracker.sendMessage(f"!V TRIAL_VAR {key} {value}")
                
                logger.debug(f"Sent marker: {marker.marker_type.value} - {marker.message}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending marker: {e}", exc_info=True)
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
