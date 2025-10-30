"""
屏幕录制模块

支持录屏和眼动数据 overlay
"""

import logging
import threading
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# 检查依赖
try:
    import cv2
    import numpy as np
    from mss import mss
    from PIL import Image
    RECORDING_AVAILABLE = True
except ImportError:
    RECORDING_AVAILABLE = False
    logger.warning("录屏依赖未安装: pip install opencv-python mss pillow numpy")


class ScreenRecorder:
    """屏幕录制器"""
    
    def __init__(self, output_dir: str = None, fps: int = 30):
        """
        初始化录制器
        
        Args:
            output_dir: 输出目录
            fps: 帧率
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./logdata/recordings")
        self.fps = fps
        self.recording = False
        self.thread = None
        self.writer = None
        self.output_file = None
        
    def start_recording(self, filename: str = None) -> bool:
        """
        开始录屏
        
        Args:
            filename: 输出文件名（不含扩展名）
            
        Returns:
            成功返回 True
        """
        if not RECORDING_AVAILABLE:
            logger.error("录屏功能不可用")
            return False
        
        if self.recording:
            logger.warning("已在录制中")
            return False
        
        try:
            # 创建输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screen_{timestamp}"
            
            self.output_file = self.output_dir / f"{filename}.mp4"
            
            # 获取屏幕尺寸
            with mss() as sct:
                monitor = sct.monitors[1]  # 主显示器
                width = monitor["width"]
                height = monitor["height"]
            
            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(
                str(self.output_file),
                fourcc,
                self.fps,
                (width, height)
            )
            
            # 开始录制线程
            self.recording = True
            self.thread = threading.Thread(target=self._record_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"录屏开始: {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"开始录屏失败: {e}")
            return False
    
    def _record_loop(self):
        """录制循环"""
        with mss() as sct:
            monitor = sct.monitors[1]
            
            while self.recording:
                try:
                    # 截图
                    screenshot = sct.grab(monitor)
                    
                    # 转换为 numpy 数组
                    frame = np.array(screenshot)
                    
                    # BGRA -> BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    # 写入视频
                    self.writer.write(frame)
                    
                    # 控制帧率
                    time.sleep(1.0 / self.fps)
                    
                except Exception as e:
                    logger.error(f"录制帧错误: {e}")
                    break
    
    def stop_recording(self) -> str:
        """
        停止录屏
        
        Returns:
            输出文件路径
        """
        if not self.recording:
            return None
        
        self.recording = False
        
        # 等待线程结束
        if self.thread:
            self.thread.join(timeout=2)
        
        # 释放写入器
        if self.writer:
            self.writer.release()
            self.writer = None
        
        logger.info(f"录屏结束: {self.output_file}")
        return str(self.output_file)


def overlay_gaze_on_video(
    video_path: str,
    edf_path: str,
    output_path: str = None,
    gaze_color: tuple = (0, 255, 0),
    gaze_radius: int = 10,
    eye: str = "right"
) -> bool:
    """
    将眼动数据叠加到录屏视频上
    
    Args:
        video_path: 原始录屏文件路径
        edf_path: EDF 眼动数据文件路径
        output_path: 输出文件路径
        gaze_color: 注视点颜色 (B, G, R)
        gaze_radius: 注视点半径
        eye: 使用哪只眼睛的数据 ("left" 或 "right"，默认 "right")
        
    Returns:
        成功返回 True
    """
    try:
        from pyedfread import read_edf
        
        # 读取 EDF 文件
        logger.info(f"读取 EDF: {edf_path}")
        # read_edf 返回三个 DataFrame: samples, events, messages
        samples, events, messages = read_edf(edf_path, ignore_samples=False)
        
        # 检查 samples 是否有效
        if samples is None or samples.empty:
            logger.error("EDF 数据中未找到有效 samples")
            return False
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("无法打开视频文件")
            return False
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"视频: {width}x{height} @ {fps}fps, {total_frames} 帧")
        
        # 输出文件
        if not output_path:
            output_path = str(Path(video_path).with_name(
                Path(video_path).stem + "_gaze.mp4"
            ))
        
        # 创建写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 获取眼动数据的起始时间
        # samples 是 pandas DataFrame
        
        if 'time' not in samples.columns:
            logger.error("EDF 样本数据中未找到 'time' 列")
            return False
        
        start_time = samples['time'].min()
        logger.info(f"EDF 起始时间: {start_time}, 样本数: {len(samples)}")
        logger.info(f"EDF samples 列名: {list(samples.columns)}")
        
        # 根据指定的眼睛选择注视点列
        eye = eye.lower()
        if eye == "right":
            gx_col = "gx_right"
            gy_col = "gy_right"
        elif eye == "left":
            gx_col = "gx_left"
            gy_col = "gy_left"
        else:
            logger.error(f"无效的眼睛参数: {eye}，必须是 'left' 或 'right'")
            return False
        
        # 检查列是否存在
        if gx_col not in samples.columns or gy_col not in samples.columns:
            logger.error(f"未找到{eye}眼注视点列: {gx_col}, {gy_col}")
            logger.error(f"可用列: {list(samples.columns)}")
            return False
        
        # 检查数据有效性
        valid_gx = samples[gx_col] > -10000
        valid_gy = samples[gy_col] > -10000
        valid_count = (valid_gx & valid_gy).sum()
        
        if valid_count == 0:
            logger.error(f"{eye}眼数据全部无效 (全为 -32768)")
            return False
        
        logger.info(f"使用 {eye} 眼数据: {gx_col}, {gy_col}")
        logger.info(f"有效样本: {valid_count}/{len(samples)} ({valid_count/len(samples)*100:.1f}%)")
        logger.info(f"时间范围: {start_time:.2f} - {samples['time'].max():.2f} ms")
        logger.info(f"视频时长: {total_frames / fps:.2f} 秒")
        
        frame_idx = 0
        logger.info("开始处理视频...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 计算当前帧对应的时间戳
            # 视频时间从0开始，EDF时间从start_time开始
            video_time_ms = (frame_idx / fps) * 1000  # 视频播放到的时间（毫秒）
            edf_time = start_time + video_time_ms  # 对应的EDF时间戳
            
            # 查找对应的眼动数据
            # 找到最接近的眼动样本
            time_diff = np.abs(samples['time'] - edf_time)
            closest_idx = time_diff.idxmin()  # 使用 idxmin() 获取索引
            
            gx = samples.loc[closest_idx, gx_col]
            gy = samples.loc[closest_idx, gy_col]
            
            # 调试：每1000帧输出一次时间对应关系
            if frame_idx % 1000 == 0:
                logger.debug(f"帧 {frame_idx}: 视频时间={video_time_ms:.2f}ms, "
                           f"EDF时间={edf_time:.2f}ms, "
                           f"最近样本时间={samples.loc[closest_idx, 'time']:.2f}ms, "
                           f"gaze=({gx:.1f}, {gy:.1f})")
            
            # 绘制注视点 (检查有效性，EyeLink 无效值通常是 -32768 或 NaN)
            if not np.isnan(gx) and not np.isnan(gy) and gx > -10000 and gy > -10000:
                x = int(gx)
                y = int(gy)
                
                # 确保坐标在范围内
                if 0 <= x < width and 0 <= y < height:
                    # 绘制圆圈（外圈）
                    cv2.circle(frame, (x, y), gaze_radius, gaze_color, 1)
                    # 绘制中心点
                    cv2.circle(frame, (x, y), 2, gaze_color, -1)
            
            # 写入帧
            out.write(frame)
            
            frame_idx += 1
            
            # 进度
            if frame_idx % 100 == 0:
                progress = (frame_idx / total_frames) * 100
                logger.info(f"处理进度: {progress:.1f}%")
        
        # 释放资源
        cap.release()
        out.release()
        
        logger.info(f"✓ Overlay 完成: {output_path}")
        return True
        
    except ImportError:
        logger.error("pyedfread 未安装: pip install pyedfread")
        return False
    except Exception as e:
        logger.error(f"Overlay 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# 全局录制器实例
screen_recorder = ScreenRecorder()

