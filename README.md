# MAIC JSON Service with EyeLink Integration

集成 EyeLink 1000 Plus 眼动仪的数据收集服务

## 快速开始

```bash
# 安装
pip install -r requirements.txt

# 配置
cp config_example.env .env
# 编辑 .env 设置 EyeLink IP 等

# 启动
python main.py
```

## 项目结构

```
├── main.py                 # 主服务
├── config.py               # 配置
├── eyelink_manager.py      # 眼动仪管理（核心API）
├── eyelink_graphics.py     # 校准界面 (pygame)
├── custom_control.py       # 实验控制
├── experiment_example.py   # 使用示例
├── models.py               # 数据模型
└── utils.py                # 工具函数
```

## 实验控制

服务启动后，如果启用自动连接会自动连接 EyeLink，否则手动连接：

```
> connect        # 连接（如果未自动连接）
> c              # 校准
> v              # 验证  
> d              # 漂移校正
> start          # 开始记录（使用 test.edf）
> marker TEST    # 发送标记
> end            # 结束并自动保存到 logdata/eyelink_data/
> status         # 查看状态
> quit           # 退出
```

## EyeLink API

### 基本操作

```python
from eyelink_manager import eyelink_manager

# 连接
eyelink_manager.connect(host_ip="100.1.1.1")

# 校准
eyelink_manager.do_calibration(1920, 1080)

# 验证
eyelink_manager.do_validation(1920, 1080)

# 漂移校正
eyelink_manager.do_drift_correct(960, 540, 1920, 1080)

# 开始记录
eyelink_manager.start_recording("test.edf")

# 发送标记
eyelink_manager.send_message("EVENT_START")

# 停止并保存
eyelink_manager.stop_recording(save_local=True, local_dir="./logdata/eyelink_data")

# 断开
eyelink_manager.disconnect()
```

### 自定义处理

在 `custom_control.py` 的 `handle_control_message()` 中处理特殊事件：

```python
def handle_control_message(event_name: str, data: dict) -> bool:
    if event_name == "SPECIAL_EVENT":
        # 处理逻辑
        return True  # 返回 True 阻止标准标记
    return False
```

## MAIC 平台集成

MAIC 平台发送数据到 `/ingest` 端点：

```bash
curl -X POST http://localhost:8123/ingest \
  -H "Content-Type: application/json" \
  -d '{"event": "trial_start", "data": {"trial_id": "1"}}'
```

自动发送标记到 EyeLink（如果已连接并记录中）。

## 配置

`.env` 文件主要配置：

```ini
# 服务端口
MAIC_PORT=8123

# EyeLink 配置
EYELINK_HOST_IP=100.1.1.1
EYELINK_DUMMY_MODE=false
EYELINK_SCREEN_WIDTH=1920
EYELINK_SCREEN_HEIGHT=1080
EYELINK_AUTO_CONNECT=true

# 注：文件名使用自动时间戳 (YYYYMMDD_HHMMSS)
```

## 文件保存

所有文件使用统一的时间戳命名（`YYYYMMDD_HHMMSS`）：

- **MAIC 消息**: `logdata/YYYYMMDD-HHMMSS_<request_id>.txt`
- **EDF 文件**: `logdata/eyelink_data/YYYYMMDD_HHMMSS.edf`
- **录屏文件**:
  - 原始: `logdata/recordings/YYYYMMDD_HHMMSS.mp4`
  - Overlay: `logdata/recordings/YYYYMMDD_HHMMSS_gaze.mp4` (带眼动轨迹)

时间戳在开始记录时自动生成，确保同一会话的所有文件使用相同的时间戳。

使用 `end` 命令自动传输、保存和处理所有文件。

## 注意事项

- 校准/验证需要 pygame 和显示器
- 文件名自动使用时间戳，无需手动配置
- dummy 模式用于无硬件测试
- 文件传输可能需要手动操作（取决于网络配置）
- 录屏功能需要安装: `pip install opencv-python mss pyedfread numpy pillow pandas`
- Overlay 处理可能需要较长时间（取决于视频长度）
- `pyedfread` 需要 SR Research EyeLink 开发工具包（Windows 平台）

## API 文档

启动后访问 http://localhost:8123/docs 查看完整 API 文档。
