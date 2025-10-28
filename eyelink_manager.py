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
    
    def start_recording(self, edf_filename: str = "test.edf") -> bool:
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
        logger.info("=" * 60)
        logger.info("开始记录眼动数据")
        logger.info("=" * 60)
        
        # 检查连接状态
        if not self.tracker:
            logger.error("❌ Tracker 对象不存在")
            logger.error("请先调用 connect() 方法")
            return False
            
        if self.status != EyeLinkStatus.CONNECTED:
            logger.error(f"❌ 当前状态不正确: {self.status.value}")
            logger.error("需要状态为 CONNECTED 才能开始记录")
            return False
        
        logger.info(f"✓ 连接状态正常")
        logger.info(f"EDF 文件名: {edf_filename}")
        
        # 验证文件名
        if len(edf_filename) > 12:  # 8.3 格式
            logger.warning(f"⚠️  文件名可能过长: {edf_filename}")
            logger.warning("EyeLink 要求 8.3 格式 (8个字符 + .edf)")
            
        try:
            with self._lock:
                # 打开 EDF 文件
                logger.info("打开 EDF 文件...")
                try:
                    self.tracker.openDataFile(edf_filename)
                    logger.info(f"✓ EDF 文件打开成功: {edf_filename}")
                    self.edf_file = edf_filename
                except Exception as e:
                    logger.error(f"❌ 打开 EDF 文件失败: {e}")
                    raise
                
                # 配置记录参数
                logger.info("配置记录参数...")
                
                commands = [
                    ("file_event_filter", "LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT"),
                    ("file_sample_data", "LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT"),
                    ("link_event_filter", "LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT"),
                    ("link_sample_data", "LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT")
                ]
                
                for cmd_name, cmd_value in commands:
                    try:
                        cmd = f"{cmd_name} = {cmd_value}"
                        logger.debug(f"  发送: {cmd}")
                        self.tracker.sendCommand(cmd)
                        logger.debug(f"  ✓ {cmd_name} 设置成功")
                    except Exception as e:
                        logger.error(f"  ❌ {cmd_name} 设置失败: {e}")
                        raise
                
                logger.info("✓ 所有记录参数配置完成")
                
                # 开始记录
                logger.info("启动记录...")
                logger.debug("  调用 startRecording(1, 1, 1, 1)")
                logger.debug("  参数含义: (record_file, record_link_events, record_link_samples, record_buttons)")
                
                try:
                    error = self.tracker.startRecording(1, 1, 1, 1)
                    if error:
                        logger.error(f"❌ startRecording 返回错误代码: {error}")
                        logger.error("错误代码含义:")
                        logger.error("  0: 成功")
                        logger.error("  其他: 参考 PyLink 文档")
                        return False
                    logger.info("✓ startRecording 调用成功")
                except Exception as e:
                    logger.error(f"❌ startRecording 调用失败: {e}")
                    raise
                
                self.recording = True
                self.status = EyeLinkStatus.RECORDING
                
                logger.info("=" * 60)
                logger.info(f"✅ 记录已开始: {edf_filename}")
                logger.info("=" * 60)
                return True
                
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ 记录启动失败: {e}")
            logger.error("=" * 60)
            logger.exception("详细错误:")
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
                logger.info("正在停止记录...")
                self.tracker.stopRecording()
                
                logger.info("正在关闭 EDF 文件...")
                self.tracker.closeDataFile()
                
                self.recording = False
                self.status = EyeLinkStatus.CONNECTED
                
                logger.info(f"✅ 记录已停止，EDF 文件: {self.edf_file}")
                # 注意：不清空 self.edf_file，保留用于文件传输
                return True
                
        except Exception as e:
            logger.error(f"❌ 停止记录失败: {e}", exc_info=True)
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
                
                # 发送主消息
                if message_to_send:
                    logger.debug(f"  → sendMessage: {message_to_send}")
                    try:
                        self.tracker.sendMessage(message_to_send)
                        logger.debug(f"  ✓ 主消息发送成功")
                    except Exception as e:
                        logger.error(f"  ❌ 主消息发送失败: {e}")
                        raise
                
                # 记录额外的试验变量
                if marker.additional_data:
                    logger.debug(f"  发送附加变量 ({len(marker.additional_data)} 个):")
                    for key, value in marker.additional_data.items():
                        var_msg = f"!V TRIAL_VAR {key} {value}"
                        logger.debug(f"    → {var_msg}")
                        try:
                            self.tracker.sendMessage(var_msg)
                            logger.debug(f"    ✓ 变量 {key} 发送成功")
                        except Exception as e:
                            logger.warning(f"    ⚠️  变量 {key} 发送失败: {e}")
                
                logger.debug(f"✅ 标记发送完成: {marker.marker_type.value}")
                logger.debug("-" * 40)
                return True
                
        except Exception as e:
            logger.error("-" * 40)
            logger.error(f"❌ 发送标记失败: {e}")
            logger.error("-" * 40)
            logger.exception("详细错误:")
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
