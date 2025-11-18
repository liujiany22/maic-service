"""
屏幕录制模块

支持录屏和眼动数据 overlay
"""

import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# 检查依赖
try:
    import cv2
    import numpy as np
    RECORDING_AVAILABLE = True
except ImportError:
    RECORDING_AVAILABLE = False

try:
    from mss import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False


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
        
    def start_recording(self, filename: str = None) -> Optional[str]:
        """
        开始录屏
        
        Args:
            filename: 输出文件名（不含扩展名）
            
        Returns:
            成功返回实际使用的文件名（不含扩展名），失败返回 None
        """
        if not RECORDING_AVAILABLE or not MSS_AVAILABLE:
            logger.error("录屏功能不可用")
            return None
        
        if self.recording:
            logger.warning("已在录制中")
            return None
        
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
            
            logger.debug(f"屏幕录制开始: {self.output_file}")
            return filename
            
        except Exception as e:
            logger.error(f"开始录屏失败: {e}")
            return None
    
    def _record_loop(self):
        """录制循环"""
        with mss() as sct:
            monitor = sct.monitors[1]  # 主显示器
            
            while self.recording:
                try:
                    # 截取屏幕
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    # 写入视频
                    self.writer.write(frame)
                    
                    # 控制帧率
                    time.sleep(1.0 / self.fps)
                    
                except Exception as e:
                    logger.error(f"录制错误: {e}")
                    time.sleep(1.0 / self.fps)
    
    def stop_recording(self) -> str:
        """停止录屏"""
        if not self.recording:
            return None
        
        self.recording = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.writer:
            self.writer.release()
            self.writer = None
        
        logger.debug(f"屏幕录制结束: {self.output_file}")
        return str(self.output_file)


def overlay_gaze_on_video(
    video_path: str,
    edf_path: str,
    output_path: str = None,
    fixation_color: tuple = (0, 0, 255),
    saccade_color: tuple = (0, 255, 255)
) -> bool:
    """
    将眼动数据叠加到录屏视频上
    
    Args:
        video_path: 原始录屏文件路径
        edf_path: EDF 眼动数据文件路径
        output_path: 输出文件路径
        gaze_color: 注视点颜色 (B, G, R)
        gaze_radius: 注视点半径
    Returns:
        成功返回 True
    """
    try:
        from pyedfread import read_edf
        
        # 读取 EDF 文件
        logger.debug(f"读取 EDF: {edf_path}")
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
        
        logger.debug(f"视频: {width}x{height} @ {fps}fps, {total_frames} 帧")
        
        # 输出文件
        if not output_path:
            output_path = str(Path(video_path).with_name(
                Path(video_path).stem + "_gaze.mp4"
            ))
        
        # 创建写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 获取眼动数据的起始时间
        if 'time' not in samples.columns:
            logger.error("EDF 样本数据中未找到 'time' 列")
            return False
        
        # 从视频文件名提取时间戳（用于匹配同步标记）
        video_filename = Path(video_path).stem
        
        # 尝试从 messages 中找到对应的屏幕录制开始标记
        screen_rec_start_time = None
        screen_rec_end_time = None
        if messages is not None and not messages.empty and 'time' in messages.columns:
            # 兼容不同列名（pyedfread 可能使用 text 或 message）
            message_col = None
            if 'text' in messages.columns:
                message_col = 'text'
            elif 'message' in messages.columns:
                message_col = 'message'

            if message_col:
                # 查找 SCREEN_REC_START_<timestamp> 标记
                screen_rec_msgs = messages[messages[message_col].astype(str).str.contains('SCREEN_REC_START', na=False)]
            else:
                screen_rec_msgs = None
            
            if screen_rec_msgs is not None and not screen_rec_msgs.empty:
                # 如果有多个，尝试匹配文件名中的时间戳
                for idx, row in screen_rec_msgs.iterrows():
                    msg_text = str(row[message_col])
                    if video_filename in msg_text or msg_text.endswith(video_filename):
                        screen_rec_start_time = row['time']
                        logger.debug(f"找到屏幕录制开始标记: {msg_text} at {screen_rec_start_time} ms")
                        break
                
                # 如果没有匹配到，使用第一个
                if screen_rec_start_time is None:
                    screen_rec_start_time = screen_rec_msgs.iloc[0]['time']
                    logger.debug(f"使用第一个屏幕录制开始标记: {screen_rec_start_time} ms")

            # 查找对应的结束标记
            if message_col:
                screen_rec_end_msgs = messages[messages[message_col].astype(str).str.contains('SCREEN_REC_END', na=False)]
            else:
                screen_rec_end_msgs = None

            if screen_rec_end_msgs is not None and not screen_rec_end_msgs.empty:
                for idx, row in screen_rec_end_msgs.iterrows():
                    msg_text = str(row[message_col])
                    if video_filename in msg_text or msg_text.endswith(video_filename):
                        screen_rec_end_time = row['time']
                        logger.debug(f"找到屏幕录制结束标记: {msg_text} at {screen_rec_end_time} ms")
                        break

                if screen_rec_end_time is None:
                    screen_rec_end_time = screen_rec_end_msgs.iloc[-1]['time']
                    logger.debug(f"使用最后一个屏幕录制结束标记: {screen_rec_end_time} ms")
        
        # 确定视频开始对应的 EDF 时间戳
        if screen_rec_start_time is None:
            logger.error("未找到屏幕录制开始标记，无法对齐视频与 EDF")
            return False
        if screen_rec_end_time is None or screen_rec_end_time <= screen_rec_start_time:
            logger.error("未找到屏幕录制结束标记，无法对齐视频与 EDF")
            return False

        video_start_edf_time = screen_rec_start_time
        edf_duration = screen_rec_end_time - screen_rec_start_time
        logger.debug(f"使用同步标记，EDF 起点: {video_start_edf_time} ms，持续: {edf_duration} ms")
        
        logger.debug(f"样本范围: {samples['time'].iloc[0]:.2f} - {samples['time'].iloc[-1]:.2f} ms, 共 {len(samples)} 条")
        logger.debug(f"EDF samples 列名: {list(samples.columns)}")

        # 预处理事件（fixation / saccade）
        fixation_events = []
        saccade_events = []
        if events is not None and not events.empty:
            for _, row in events.iterrows():
                event_type = str(row.get("type", "")).lower()
                try:
                    start = float(row.get("start"))
                    end = float(row.get("end"))
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(start) or not np.isfinite(end) or end <= start:
                    continue

                if event_type == "fixation":
                    # 使用平均坐标，如果缺失则退回起始坐标
                    x = row.get("gavx")
                    y = row.get("gavy")
                    if x is None or not np.isfinite(x):
                        x = row.get("gstx")
                    if y is None or not np.isfinite(y):
                        y = row.get("gsty")
                    if x is None or y is None:
                        continue
                    x = float(x)
                    y = float(y)
                    if not (np.isfinite(x) and np.isfinite(y)):
                        continue
                    duration = end - start
                    fixation_events.append({
                        "start": start,
                        "end": end,
                        "x": x,
                        "y": y,
                        "duration": duration
                    })
                elif event_type == "saccade":
                    sx = row.get("gstx")
                    sy = row.get("gsty")
                    ex = row.get("genx")
                    ey = row.get("geny")
                    if None in (sx, sy, ex, ey):
                        continue
                    sx = float(sx)
                    sy = float(sy)
                    ex = float(ex)
                    ey = float(ey)
                    if not (np.isfinite(sx) and np.isfinite(sy) and np.isfinite(ex) and np.isfinite(ey)):
                        continue
                    saccade_events.append({
                        "start": start,
                        "end": end,
                        "sx": sx,
                        "sy": sy,
                        "ex": ex,
                        "ey": ey
                    })

        fixation_events.sort(key=lambda ev: ev["start"])
        saccade_events.sort(key=lambda ev: ev["start"])
        fixation_idx = 0
        saccade_idx = 0
        
        frame_idx = 0
        base_radius = 4
        max_radius = 16
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 计算当前帧对应的时间戳
            # 视频时间从0开始，对应EDF时间从video_start_edf_time开始
            edf_time = video_start_edf_time + edf_duration * (frame_idx / (total_frames - 1))

            # 绘制当前 fixation
            while fixation_idx < len(fixation_events) and edf_time > fixation_events[fixation_idx]["end"]:
                fixation_idx += 1
            if fixation_idx < len(fixation_events):
                fix = fixation_events[fixation_idx]
                if fix["start"] <= edf_time <= fix["end"]:
                    fx = int(fix["x"])
                    fy = int(fix["y"])
                    if 0 <= fx < width and 0 <= fy < height:
                        radius = min(base_radius + int(fix["duration"] / 50), max_radius)
                        cv2.circle(frame, (fx, fy), radius, fixation_color, 2)
                        cv2.circle(frame, (fx, fy), 3, fixation_color, -1)

            # 绘制当前 saccade（用箭头表示当前进行的扫视）
            while saccade_idx < len(saccade_events) and edf_time > saccade_events[saccade_idx]["end"]:
                saccade_idx += 1
            if saccade_idx < len(saccade_events):
                sac = saccade_events[saccade_idx]
                if sac["start"] <= edf_time <= sac["end"]:
                    sx = int(sac["sx"])
                    sy = int(sac["sy"])
                    ex = int(sac["ex"])
                    ey = int(sac["ey"])
                    if (0 <= sx < width and 0 <= sy < height and
                            0 <= ex < width and 0 <= ey < height):
                        cv2.arrowedLine(frame, (sx, sy), (ex, ey), saccade_color, 2, tipLength=0.2)
            
            # 写入帧
            out.write(frame)
            frame_idx += 1
            
            # 进度 (每 30% 输出一次)
            progress = (frame_idx / total_frames) * 100
            if frame_idx % (total_frames // 3) == 0:
                logger.debug(f"Overlay 进度: {progress:.0f}%")
        
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

