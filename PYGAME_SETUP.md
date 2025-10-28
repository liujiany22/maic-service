# Pygame 校准界面说明

## 概述

本项目使用 pygame 实现 EyeLink 的校准和验证界面。这是一个标准的 PyLink + pygame 集成方案。

## 安装

```bash
pip install pygame
```

## 功能说明

### 校准界面功能

当你输入 `c` 进行校准时，会：

1. **创建全屏窗口**: pygame 会创建一个灰色背景的全屏窗口
2. **显示校准目标**: 在校准点位置显示白色圆圈（外圈+内圈）
3. **接受键盘输入**: 
   - `ESC` - 退出校准
   - `Enter` - 确认/继续
   - `空格` - 接受当前点
   - 其他按键根据 EyeLink 校准模式处理

### 校准流程

```
实验控制 > c
↓
pygame 创建全屏窗口
↓
EyeLink 显示校准点（通常 9 点或 5 点）
↓
被试注视校准点，按空格键确认
↓
完成所有点的校准
↓
显示校准结果
↓
按 Enter 接受或 ESC 重新校准
```

### 验证流程

```
实验控制 > v
↓
进入校准界面
↓
选择 "Validate" 选项（按 'V' 键）
↓
类似校准流程，但用于验证准确性
```

## 图形界面类说明

### EyeLinkCoreGraphicsPygame

这是核心图形界面类，继承自 `pylink.EyeLinkCustomDisplay`。

**主要方法：**

1. `setup_cal_display()` - 设置校准显示
   - 创建全屏窗口
   - 设置背景色

2. `draw_cal_target(x, y)` - 绘制校准目标
   - 在指定位置绘制圆圈
   - 外圈直径 40 像素
   - 内圈直径 10 像素

3. `get_input_key()` - 获取键盘输入
   - 处理 ESC、Enter、空格等按键
   - 返回 PyLink 键盘事件

4. `clear_cal_display()` - 清除显示
   - 填充背景色
   - 刷新显示

5. `exit_cal_display()` - 退出校准
   - 清理显示

## 自定义颜色

在 `eyelink_graphics.py` 中可以自定义颜色：

```python
class EyeLinkCoreGraphicsPygame(pylink.EyeLinkCustomDisplay):
    def __init__(self, width, height):
        # 颜色定义
        self.foreground_color = (255, 255, 255)  # 校准点颜色（白色）
        self.background_color = (128, 128, 128)  # 背景色（灰色）
```

可以修改为：
- `(0, 0, 0)` - 黑色背景
- `(255, 255, 255)` - 白色背景
- `(255, 0, 0)` - 红色校准点
- 等等

## 自定义校准点样式

在 `draw_cal_target()` 方法中修改：

```python
def draw_cal_target(self, x, y):
    """绘制校准目标"""
    if self.screen:
        self.clear_cal_display()
        
        # 外圆
        pygame.draw.circle(
            self.screen,
            self.foreground_color,
            (int(x), int(y)),
            20,  # 外圆半径
            2    # 线宽（0=填充）
        )
        
        # 内圆
        pygame.draw.circle(
            self.screen,
            self.foreground_color,
            (int(x), int(y)),
            5,   # 内圆半径
            0    # 0=填充
        )
        
        pygame.display.flip()
```

可以修改为：
- 不同大小的圆圈
- 十字形目标
- 点状目标
- 动画效果

## 屏幕分辨率设置

在 `.env` 文件中设置：

```ini
EYELINK_SCREEN_WIDTH=1920
EYELINK_SCREEN_HEIGHT=1080
```

确保这个分辨率与你的显示器匹配。

## 常见问题

### Q: 校准窗口不是全屏？

A: 检查 pygame 版本，确保使用 `pygame.FULLSCREEN` 标志：

```python
self.screen = pygame.display.set_mode(
    self.size,
    pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
)
```

### Q: 校准点位置不准确？

A: 确保 `.env` 中的屏幕分辨率设置正确：
- 使用实际显示器的分辨率
- 不要使用缩放后的分辨率

### Q: 在远程服务器上无法使用？

A: pygame 需要显示器。在无显示器环境下：
1. 使用 dummy 模式：`EYELINK_DUMMY_MODE=true`
2. 或使用虚拟显示（xvfb）

### Q: 如何添加声音提示？

A: 在 `play_beep()` 方法中添加：

```python
def play_beep(self, beep_type):
    """播放提示音"""
    import pygame.mixer
    
    if beep_type == pylink.CAL_TARG_BEEP:
        # 播放目标音
        pass
    elif beep_type == pylink.CAL_ERR_BEEP:
        # 播放错误音
        pass
    # ... 更多提示音
```

### Q: 如何显示相机画面？

A: 需要实现 `draw_image_line()` 方法，这较为复杂。建议使用 EyeLink Data Viewer 查看相机画面。

## 便捷函数

### do_tracker_setup()

封装了完整的校准流程：

```python
from eyelink_graphics import do_tracker_setup

success = do_tracker_setup(tracker, width, height)
```

内部会：
1. 设置 pygame 图形环境
2. 调用 `tracker.doTrackerSetup()`
3. 处理校准流程

### do_drift_correct()

漂移校正：

```python
from eyelink_graphics import do_drift_correct

# 在屏幕中心做漂移校正
success = do_drift_correct(
    tracker, 
    width // 2,   # x 坐标
    height // 2,  # y 坐标
    draw=1,       # 绘制目标
    allow_setup=1 # 允许进入 setup
)
```

## 调试

### 启用调试日志

在启动前设置日志级别（已经是 DEBUG）：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 测试图形界面

可以单独测试 pygame：

```python
import pygame
pygame.init()
screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
screen.fill((128, 128, 128))
pygame.draw.circle(screen, (255, 255, 255), (960, 540), 20, 2)
pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()
```

## 参考资料

- [SR Research PyLink 文档](https://www.sr-research.com/support/)
- [pygame 文档](https://www.pygame.org/docs/)
- [EyeLink 编程指南](https://www.sr-research.com/support/thread-13.html)

## 技术细节

### PyLink Custom Display

PyLink 提供了 `EyeLinkCustomDisplay` 基类，允许使用任何图形库（pygame、psychopy、pyglet等）。

**必须实现的方法：**
- `setup_cal_display()`
- `exit_cal_display()`
- `clear_cal_display()`
- `erase_cal_target()`
- `draw_cal_target(x, y)`
- `get_input_key()`

**可选方法：**
- `play_beep(beep_type)`
- `image_title(title)`
- `draw_image_line(width, line, totlines, buff)`
- `set_image_palette(r, g, b)`

### pygame 全屏模式

使用以下标志获得最佳性能：

```python
pygame.FULLSCREEN    # 全屏模式
pygame.HWSURFACE     # 硬件表面（更快）
pygame.DOUBLEBUF     # 双缓冲（防止闪烁）
```

### 坐标系统

- EyeLink 使用屏幕坐标系统
- 原点 (0, 0) 在左上角
- x 向右增加，y 向下增加
- 确保 pygame 窗口坐标与 EyeLink 坐标匹配

## 高级自定义

如果需要更复杂的功能（如动画校准点、渐变背景等），可以直接修改 `eyelink_graphics.py` 中的 `EyeLinkCoreGraphicsPygame` 类。

所有 pygame 的功能都可以使用，例如：
- 图像加载和显示
- 文字渲染
- 动画效果
- 声音播放
- 等等

只要确保实现了必需的接口方法即可。

