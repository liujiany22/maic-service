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

from models import EyeLinkMarker, EyeLinkStatus, EyeLinkStatusResponse, MarkerType

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
        self.current_video_label: Optional[str] = None  # 当前屏幕录制标签
        self.error_message: Optional[str] = None
        self.screen_width: int = 1920  # 屏幕宽度
        self.screen_height: int = 1080  # 屏幕高度
        self._lock = threading.RLock()  # 使用可重入锁，允许同一线程多次获取
        
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
                
                # 创建连接
                if dummy_mode:
                    logger.info("使用虚拟模式")
                    self.tracker = pylink.EyeLink(None)
                else:
                    logger.info(f"连接到设备: {host_ip}")
                    self.tracker = pylink.EyeLink(host_ip)
                
                
                # 保存屏幕尺寸供后续使用
                self.screen_width = screen_width
                self.screen_height = screen_height
                                
                self.status = EyeLinkStatus.CONNECTED
                self.error_message = None
                logger.info("EyeLink 连接成功")
                self.current_video_label = None
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
        
        logger.info(f"开始记录: {edf_short_name} (会话:{session_timestamp})")
        
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
                
                # 等待数据流稳定（100ms）
                import pylink
                pylink.pumpDelay(100)
                
                self.recording = True
                self.status = EyeLinkStatus.RECORDING
                logger.info("EyeLink 记录已开始")
            
            # 启动屏幕录制（在锁外面执行，避免长时间持有锁）
            if enable_screen_recording:
                try:
                    from screen_recorder import screen_recorder
                    video_label = screen_recorder.start_recording()
                    if video_label:
                        logger.debug("屏幕录制已开始")
                        self.send_message(f"SCREEN_REC_START_{video_label}")
                        self.current_video_label = video_label
                    else:
                        logger.warning("屏幕录制启动失败: 未获取有效文件名")
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
                logger.info("停止记录")

                # 在停止录制前记录屏幕录制结束标记
                if self.current_video_label:
                    self.send_message(f"SCREEN_REC_END_{self.current_video_label}")

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
                        logger.debug(f"EDF 已保存: {local_file}")
                        saved_edf_path = local_file  # 保存实际路径
                    except Exception as e:
                        logger.error(f"EDF传输失败: {e}")
                
                self.tracker.closeDataFile()
                self.recording = False
                self.status = EyeLinkStatus.CONNECTED
                logger.info("EyeLink 记录已停止")
                
                # 解析 EDF 为 CSV
                if saved_edf_path:
                    try:
                        logger.debug("解析 EDF 为 CSV")
                        from pyedfread import read_edf
                        from pathlib import Path
                        
                        if saved_edf_path.exists():
                            # 读取 EDF
                            samples, events, messages = read_edf(str(saved_edf_path), ignore_samples=False)
                            
                            # 保存 CSV
                            csv_base = saved_edf_path.parent / self.session_timestamp
                            
                            if samples is not None and not samples.empty:
                                samples_csv = f"{csv_base}_samples.csv"
                                samples.to_csv(samples_csv, index=False)
                            
                            if events is not None and not events.empty:
                                events_csv = f"{csv_base}_events.csv"
                                events.to_csv(events_csv, index=False)
                            
                            if messages is not None and not messages.empty:
                                messages_csv = f"{csv_base}_messages.csv"
                                messages.to_csv(messages_csv, index=False)
                        else:
                            logger.warning(f"EDF 文件未找到: {saved_edf_path}")
                    
                    except Exception as e:
                        logger.error(f"CSV 导出失败: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 停止屏幕录制并处理 overlay
                try:
                    from screen_recorder import screen_recorder, overlay_gaze_on_video
                    
                    # 停止录屏
                    video_path = screen_recorder.stop_recording()
                    
                    # 如果有录屏且有 EDF 文件，进行 overlay 处理
                    if video_path and saved_edf_path:
                        
                        from pathlib import Path
                        
                        # 使用实际保存的 EDF 文件路径
                        if saved_edf_path.exists():
                            # Overlay视频：使用时间戳_gaze.mp4
                            overlay_output = str(Path(video_path).parent / f"{self.session_timestamp}_gaze.mp4")
                            
                            # 导入配置
                            import config
                            
                            success = overlay_gaze_on_video(
                                video_path=video_path,
                                edf_path=str(saved_edf_path),
                                output_path=overlay_output
                            )
                            
                            if not success:
                                logger.error("Overlay 处理失败")
                        else:
                            logger.warning(f"EDF 文件未找到: {saved_edf_path}")
                    elif video_path:
                        logger.debug("录屏已保存 (无 Overlay)")
                
                except Exception as e:
                    logger.error(f"录屏处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                return True
                
        except Exception as e:
            logger.error(f"停止记录失败: {e}")
            self.current_video_label = None
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
    
    def open_setup(self) -> bool:
        """打开 EyeLink 图形界面，用户可手动执行校准/验证/漂移校正"""
        if not self.tracker:
            logger.error("未连接到 EyeLink")
            return False

        try:
            logger.info("打开 EyeLink 设置界面")

            # 设置采样率（按照 SR Research 建议）
            self.tracker.sendCommand("sample_rate 1000")

            
            pylink.closeGraphics()
            pylink.openGraphics()

            # 设置统一的图形参数
            pylink.setCalibrationColors((0, 0, 0), (128, 128, 128))
            pylink.setTargetSize(int(self.screen_width / 70.0), int(self.screen_width / 300.0))
            pylink.setCalibrationSounds("", "", "")
            pylink.setDriftCorrectSounds("", "", "")

            # 进入设置界面（用户可按 C/V/空格/ESC）
            self.tracker.doTrackerSetup()

            pylink.closeGraphics()
            logger.info("已关闭 EyeLink 设置界面")
            return True

        except Exception as e:
            logger.error(f"打开设置界面失败: {e}")
            import traceback
            traceback.print_exc()

            try:
                pylink.closeGraphics()
            except:
                pass

            return False
    
    def send_message(self, message: str) -> bool:
        """
        发送简单消息到 EyeLink
        
        Args:
            message: 消息内容（最大 130 个字符）
            
        Returns:
            成功返回 True
            
        注意:
            - 消息会被写入 EDF 文件
            - 最大长度 130 字符，超出部分会被截断
            - 只能在 CONNECTED 或 RECORDING 状态下发送
        """
        # 检查 tracker 是否存在
        if not self.tracker:
            logger.warning("无法发送消息: 未连接")
            return False
        
        # 检查状态
        if self.status not in [EyeLinkStatus.CONNECTED, EyeLinkStatus.RECORDING]:
            logger.warning(f"无法发送消息: 状态不正确 ({self.status.value})")
            return False
        
        # 检查消息长度
        if len(message) > 130:
            logger.warning(f"消息过长 ({len(message)} 字符)，将被截断为 130 字符")
        
        try:
            with self._lock:
                # sendMessage 返回值：0=成功无截断，1=成功但截断，异常=失败
                result = self.tracker.sendMessage(message)
                
                if result == 0:
                    logger.debug(f"消息已发送: {message}")
                elif result == 1:
                    logger.warning(f"消息已发送但被截断: {message[:130]}...")
                else:
                    logger.error(f"消息发送失败，返回值: {result}")
                    return False
                    
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
