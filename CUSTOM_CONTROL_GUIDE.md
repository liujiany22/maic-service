# 自定义控制指南

## 概述

`custom_control.py` 是为你提供的自定义控制区域。你可以在这个文件中编写代码来控制 EyeLink 眼动仪，实现：

- 键盘输入控制
- 响应特定的网络消息
- 定时任务
- 直接调用 PyLink API

## 快速开始

### 方式 1: 启用键盘控制

1. 打开 `custom_control.py`
2. 找到 `keyboard_control_example()` 函数
3. 取消注释函数内部的代码（删除 `#` 符号）
4. 在 `initialize_custom_control()` 中取消注释 `keyboard_control_example()`
5. 重启服务

启用后，你可以在终端输入命令：

```
EyeLink > start       # 开始记录
EyeLink > stop        # 停止记录
EyeLink > calibrate   # 校准（需要图形界面）
EyeLink > drift       # 漂移校正（需要图形界面）
EyeLink > status      # 查看状态
EyeLink > marker      # 发送测试标记
EyeLink > quit        # 退出
```

### 方式 2: 响应 MAIC 平台的控制消息

1. 打开 `custom_control.py`
2. 找到 `handle_control_message()` 函数
3. 取消注释示例代码或添加你自己的逻辑

示例 - 开始记录：

```python
def handle_control_message(event_name: str, data: dict) -> bool:
    if event_name == "EYELINK_START_RECORDING":
        logger.info("收到开始记录命令")
        eyelink_manager.start_recording()
        return True  # 返回 True 表示已处理
    
    return False  # 返回 False 继续标准流程
```

然后 MAIC 平台发送：

```json
{
  "event": "EYELINK_START_RECORDING",
  "data": {}
}
```

### 方式 3: 直接使用 PyLink API

你可以直接访问 PyLink tracker 对象，调用所有 PyLink API：

```python
# 获取 tracker
tracker = get_eyelink_tracker()

if tracker:
    # 发送命令
    tracker.sendCommand("record_status_message 'Recording Trial 1'")
    
    # 发送消息
    tracker.sendMessage("TRIAL_START")
    
    # 设置变量
    tracker.sendMessage("!V TRIAL_VAR trial_id 001")
    
    # 校准（需要图形界面）
    # tracker.doTrackerSetup()
    
    # 漂移校正（需要图形界面）
    # tracker.doDriftCorrect(width//2, height//2, 1, 1)
```

## 常用场景

### 场景 1: 实验开始时自动校准

```python
def initialize_custom_control():
    """初始化时执行"""
    logger.info("初始化自定义控制...")
    
    # 如果连接成功，自动进入校准
    if eyelink_manager.get_status().connected:
        logger.info("准备校准...")
        # tracker = get_eyelink_tracker()
        # if tracker:
        #     tracker.doTrackerSetup()
```

### 场景 2: 响应实验事件自动控制记录

```python
def handle_control_message(event_name: str, data: dict) -> bool:
    # 实验开始 - 自动开始记录
    if event_name == "EXPERIMENT_START":
        logger.info("实验开始，自动开始记录")
        eyelink_manager.start_recording()
        return True
    
    # 实验结束 - 自动停止记录
    elif event_name == "EXPERIMENT_END":
        logger.info("实验结束，自动停止记录")
        eyelink_manager.stop_recording()
        return True
    
    # Block 开始 - 发送标记
    elif event_name == "BLOCK_START":
        block_id = data.get("block_id", "unknown")
        quick_marker(f"BLOCK_START_{block_id}")
        return False  # 继续发送标准标记
    
    return False
```

### 场景 3: 每个 trial 前自动漂移校正

```python
def handle_control_message(event_name: str, data: dict) -> bool:
    if event_name == "TRIAL_START":
        trial_id = data.get("trial_id")
        logger.info(f"Trial {trial_id} 开始")
        
        # 发送标记
        quick_marker(f"TRIAL_START_{trial_id}")
        
        # 可选：每 N 个 trial 做一次漂移校正
        # trial_num = int(trial_id.split('_')[-1])
        # if trial_num % 5 == 0:  # 每 5 个 trial
        #     tracker = get_eyelink_tracker()
        #     if tracker:
        #         tracker.doDriftCorrect(960, 540, 1, 1)
        
        return False  # 继续发送标准标记
    
    return False
```

### 场景 4: 定期检查和自动重连

```python
def start_periodic_task():
    """周期性任务"""
    import time
    
    def periodic_check():
        while True:
            time.sleep(30)  # 每 30 秒检查一次
            
            status = eyelink_manager.get_status()
            
            # 检查连接状态
            if not status.connected:
                logger.warning("EyeLink 连接丢失，尝试重连...")
                # 尝试重连逻辑
            
            # 检查记录状态
            elif status.recording:
                logger.debug(f"记录中: {status.edf_file}")
    
    # 启动后台线程
    task_thread = threading.Thread(target=periodic_check, daemon=True)
    task_thread.start()
    logger.info("周期性检查任务已启动")

def initialize_custom_control():
    start_periodic_task()
```

## 可用的 API

### EyeLink 管理器方法

```python
from eyelink_manager import eyelink_manager

# 连接
eyelink_manager.connect(host_ip, dummy_mode, screen_width, screen_height)

# 断开
eyelink_manager.disconnect()

# 开始记录
eyelink_manager.start_recording(edf_filename="test.edf")

# 停止记录
eyelink_manager.stop_recording()

# 发送标记
from models import EyeLinkMarker, MarkerType
from datetime import datetime, timezone

marker = EyeLinkMarker(
    marker_type=MarkerType.MESSAGE,
    message="MY_MARKER",
    timestamp=datetime.now(timezone.utc)
)
eyelink_manager.send_marker(marker)

# 获取状态
status = eyelink_manager.get_status()
print(status.connected)   # 是否连接
print(status.recording)   # 是否记录中
print(status.edf_file)    # EDF 文件名
```

### 便捷函数

```python
from custom_control import get_eyelink_tracker, quick_marker

# 快速发送标记
quick_marker("TRIAL_START")

# 获取 tracker 对象
tracker = get_eyelink_tracker()
if tracker:
    tracker.sendMessage("CUSTOM_MESSAGE")
```

### PyLink API（部分常用方法）

```python
tracker = get_eyelink_tracker()

# 发送命令
tracker.sendCommand("command_string")

# 发送消息
tracker.sendMessage("message_string")

# 校准
tracker.doTrackerSetup()

# 漂移校正
tracker.doDriftCorrect(x, y, draw_target, allow_setup)

# 设置屏幕坐标
tracker.sendCommand(f"screen_pixel_coords 0 0 {width-1} {height-1}")

# 记录状态消息
tracker.sendCommand("record_status_message 'Status Text'")
```

更多 PyLink API 请参考 [SR Research 官方文档](https://www.sr-research.com/support/)。

## 注意事项

1. **图形界面要求**：`doTrackerSetup()` 和 `doDriftCorrect()` 需要图形界面（通常是 pygame 或 psychopy）
2. **线程安全**：在后台线程中操作 EyeLink 时要注意线程安全
3. **错误处理**：建议添加 try-except 来捕获可能的异常
4. **日志记录**：使用 `logger.info()` 等记录重要操作，方便调试

## 调试技巧

### 查看 EyeLink 状态

```python
status = eyelink_manager.get_status()
logger.info(f"状态: {status.status.value}")
logger.info(f"连接: {status.connected}")
logger.info(f"记录: {status.recording}")
logger.info(f"文件: {status.edf_file}")
```

### 测试标记发送

```python
quick_marker("TEST_MARKER")
```

### 检查 PyLink 是否可用

```python
from eyelink_manager import EYELINK_AVAILABLE

if EYELINK_AVAILABLE:
    logger.info("PyLink 可用")
else:
    logger.warning("PyLink 不可用")
```

## 示例：完整的实验控制流程

```python
def initialize_custom_control():
    """完整的实验控制示例"""
    
    logger.info("初始化实验控制...")
    
    # 1. 等待实验者准备
    # input("按 Enter 开始实验...")
    
    # 2. 校准
    # tracker = get_eyelink_tracker()
    # if tracker:
    #     logger.info("开始校准...")
    #     tracker.doTrackerSetup()
    
    # 3. 开始记录
    # logger.info("开始记录...")
    # eyelink_manager.start_recording()
    
    # 4. 发送实验开始标记
    # quick_marker("EXPERIMENT_START")
    
    logger.info("实验控制初始化完成")

def handle_control_message(event_name: str, data: dict) -> bool:
    """处理实验事件"""
    
    # Block 开始
    if event_name == "BLOCK_START":
        block_id = data.get("block_id")
        quick_marker(f"BLOCK_START_{block_id}")
        
    # Trial 开始
    elif event_name == "TRIAL_START":
        trial_id = data.get("trial_id")
        quick_marker(f"TRIAL_START_{trial_id}")
        
        # 发送试次变量
        tracker = get_eyelink_tracker()
        if tracker:
            tracker.sendMessage(f"!V TRIAL_VAR trial_id {trial_id}")
            condition = data.get("condition", "unknown")
            tracker.sendMessage(f"!V TRIAL_VAR condition {condition}")
    
    # 刺激呈现
    elif event_name == "STIMULUS_ONSET":
        quick_marker("STIMULUS_ONSET")
    
    # 反应
    elif event_name == "RESPONSE":
        response = data.get("response")
        rt = data.get("rt")
        quick_marker(f"RESPONSE_{response}_RT_{rt}")
    
    # Trial 结束
    elif event_name == "TRIAL_END":
        quick_marker("TRIAL_END")
    
    # 实验结束
    elif event_name == "EXPERIMENT_END":
        quick_marker("EXPERIMENT_END")
        logger.info("停止记录...")
        eyelink_manager.stop_recording()
        return True
    
    return False  # 继续发送标准标记
```

## 需要帮助？

- 查看 `custom_control.py` 中的详细注释
- 参考 [EyeLink 官方文档](https://www.sr-research.com/support/)
- 查看 `debug_eyelink.py` 了解如何测试连接
- 使用 `logger.debug()` 添加调试信息

