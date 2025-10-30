"""
EyeLink 图形界面模块

使用 pygame 实现 EyeLink 校准、验证等需要图形界面的功能
"""

import logging
import sys

logger = logging.getLogger(__name__)

# 检查依赖库
try:
    import pylink
    PYLINK_AVAILABLE = True
except ImportError:
    PYLINK_AVAILABLE = False
    logger.warning("PyLink 不可用")

try:
    import pygame
    from pygame.locals import *
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame 不可用，图形界面功能将被禁用")


class EyeLinkCoreGraphicsPygame(pylink.EyeLinkCustomDisplay):
    """
    EyeLink 自定义图形界面类
    
    继承自 pylink.EyeLinkCustomDisplay，使用 pygame 实现
    用于 EyeLink 的校准、验证等图形界面功能
    """
    
    def __init__(self, width, height):
        """
        初始化图形界面
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
        """
        pylink.EyeLinkCustomDisplay.__init__(self)
        
        self.width = width
        self.height = height
        self.screen = None
        self.size = (width, height)
        
        # 颜色定义
        self.foreground_color = (255, 255, 255)  # 白色
        self.background_color = (128, 128, 128)  # 灰色
        
        logger.info(f"EyeLink 图形界面初始化: {width}x{height}")
    
    def setup_cal_display(self):
        """设置校准显示"""
        logger.info(f">>> setup_cal_display 被调用, size={self.size}")
        
        if self.screen is None:
            self.screen = pygame.display.set_mode(
                self.size,
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            )
            logger.info(f"✓ pygame 窗口已创建: {self.size}")
        
        self.screen.fill(self.background_color)
        pygame.display.flip()
        logger.info("✓ 校准显示已设置")
    
    def exit_cal_display(self):
        """退出校准显示"""
        self.clear_cal_display()
        logger.debug("退出校准显示")
    
    def record_abort_hide(self):
        """隐藏中止记录的界面"""
        pass
    
    def clear_cal_display(self):
        """清除校准显示"""
        if self.screen:
            self.screen.fill(self.background_color)
            pygame.display.flip()
    
    def erase_cal_target(self):
        """擦除校准目标"""
        self.clear_cal_display()
    
    def draw_cal_target(self, x, y):
        """
        绘制校准目标
        
        Args:
            x: 目标 x 坐标
            y: 目标 y 坐标
        """
        logger.info(f">>> draw_cal_target 被调用: x={x}, y={y}, screen={self.screen is not None}")
        
        if self.screen:
            self.clear_cal_display()
            
            # 绘制外圆
            pygame.draw.circle(
                self.screen,
                self.foreground_color,
                (int(x), int(y)),
                20,
                2
            )
            
            # 绘制内圆
            pygame.draw.circle(
                self.screen,
                self.foreground_color,
                (int(x), int(y)),
                5,
                0
            )
            
            pygame.display.flip()
            logger.info(f"✓ 校准目标已绘制: ({x}, {y})")
        else:
            logger.error("screen 为 None，无法绘制校准目标")
    
    def play_beep(self, beep_type):
        """
        播放提示音
        
        Args:
            beep_type: 提示音类型
        """
        # 可以使用 pygame.mixer 播放声音
        # 这里简化处理，不播放声音
        pass
    
    def get_input_key(self):
        """
        获取键盘输入
        
        Returns:
            pylink.KeyInput 对象，或 None
        """
        keys = []
        
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                key = event.key
                mod = event.mod
                
                # ESC 键
                if key == K_ESCAPE:
                    return pylink.KeyInput(pylink.ESC_KEY, 0)
                
                # Return/Enter 键
                elif key == K_RETURN:
                    return pylink.KeyInput(pylink.ENTER_KEY, 0)
                
                # 空格键
                elif key == K_SPACE:
                    return pylink.KeyInput(ord(' '), 0)
                
                # 其他键
                else:
                    return pylink.KeyInput(key, mod)
            
            elif event.type == QUIT:
                return pylink.KeyInput(pylink.ESC_KEY, 0)
        
        return None
    
    def alert_printf(self, message):
        """
        显示警告消息
        
        Args:
            message: 消息内容
        """
        logger.warning(f"EyeLink Alert: {message}")
    
    def image_title(self, title):
        """
        设置图像标题
        
        Args:
            title: 标题文本
        """
        pass
    
    def draw_image_line(self, width, line, totlines, buff):
        """
        绘制图像行（用于相机画面等）
        
        Args:
            width: 图像宽度
            line: 当前行号
            totlines: 总行数
            buff: 图像数据缓冲区
        """
        pass
    
    def set_image_palette(self, r, g, b):
        """
        设置图像调色板
        
        Args:
            r, g, b: RGB 颜色数组
        """
        pass


def setup_graphics(tracker, width, height):
    """
    设置 EyeLink 图形界面
    
    参考 SR Research 官方示例 link_sample.py 的实现流程
    
    Args:
        tracker: PyLink tracker 对象
        width: 屏幕宽度
        height: 屏幕高度
        
    Returns:
        成功返回 True，失败返回 False
    """
    if not PYGAME_AVAILABLE:
        logger.error("pygame 不可用，无法设置图形界面")
        return False
    
    if not PYLINK_AVAILABLE:
        logger.error("PyLink 不可用，无法设置图形界面")
        return False
    
    try:
        # Step 1: 使用 PyLink 默认图形界面（不使用自定义类）
        # 参考 link_sample.py 第 362 行
        logger.info(f"初始化 PyLink 默认图形界面: {width}x{height}")
        pylink.openGraphics((width, height), 32)
        
        logger.info("✓ openGraphics 完成")
        
        # Step 2: 在 openGraphics 之后设置校准参数
        # 参考 link_sample.py 第 420-428 行
        
        # 设置校准颜色（背景黑色，目标灰色）
        pylink.setCalibrationColors((0, 0, 0), (128, 128, 128))
        logger.debug("✓ setCalibrationColors 完成")
        
        # 设置目标大小
        outer_size = int(width / 70.0)   # 外圈约 27 像素
        inner_size = int(width / 300.0)  # 内圈约 6 像素
        pylink.setTargetSize(outer_size, inner_size)
        logger.debug("✓ setTargetSize 完成")
        
        # 设置声音（静音）
        pylink.setCalibrationSounds("", "", "")
        pylink.setDriftCorrectSounds("", "", "")
        logger.debug("✓ 声音设置完成")
        
        logger.info("EyeLink 图形界面设置成功")
        return True
        
    except Exception as e:
        logger.error(f"设置图形界面失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def close_graphics():
    """关闭图形界面"""
    try:
        if PYLINK_AVAILABLE:
            pylink.closeGraphics()
        
        if PYGAME_AVAILABLE:
            pygame.quit()
        
        logger.info("图形界面已关闭")
        
    except Exception as e:
        logger.error(f"关闭图形界面时出错: {e}")


def do_tracker_setup(tracker, width, height):
    """
    执行 EyeLink 校准设置
    
    这是一个便捷函数，封装了完整的校准流程
    
    Args:
        tracker: PyLink tracker 对象
        width: 屏幕宽度
        height: 屏幕高度
        
    Returns:
        成功返回 True，失败返回 False
    """
    if not tracker:
        logger.error("tracker 对象为 None")
        return False
    
    try:
        # Step 1: 设置图形界面和校准参数
        success = setup_graphics(tracker, width, height)
        if not success:
            return False
        
        # Step 2: 进入校准模式
        # 参考 link_sample.py 第 431 行
        logger.info("进入校准模式...")
        tracker.doTrackerSetup()
        
        logger.info("✓ 校准完成")
        return True
        
    except Exception as e:
        logger.error(f"校准过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 不在这里关闭图形界面，让 close_graphics() 统一处理
        pass


def do_drift_correct(tracker, x, y, draw=1, allow_setup=1):
    """
    执行漂移校正
    
    Args:
        tracker: PyLink tracker 对象
        x: 校正点 x 坐标
        y: 校正点 y 坐标
        draw: 是否绘制目标
        allow_setup: 是否允许进入 setup
        
    Returns:
        成功返回 True，失败返回 False
    """
    if not tracker:
        logger.error("tracker 对象为 None")
        return False
    
    try:
        logger.info(f"执行漂移校正: ({x}, {y})")
        result = tracker.doDriftCorrect(x, y, draw, allow_setup)
        
        if result == 0:
            logger.info("漂移校正成功")
            return True
        else:
            logger.warning(f"漂移校正返回: {result}")
            return False
            
    except Exception as e:
        logger.error(f"漂移校正出错: {e}")
        return False

