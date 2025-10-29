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

## MAIC 平台集成

MAIC 平台发送数据到 `/ingest` 端点：

```bash
curl -X POST http://localhost:8123/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "learning_stage_id": "68d2bd81246d68cef5e3308f",
    "label": "P",
    "update_params": {
      "page_number": 5,
      "enter_type": "up_enter",
      "timestamp": "2025-10-24 21:55:48.973437"
    },
    "request_id": "cc44114a4f1e4dc8b5320a71ca5caf2a"
  }'
```

系统会：
1. 保存完整数据到 `logdata/YYYYMMDD-HHMMSS_<request_id>.txt`
2. **只发送 `request_id` 作为 EyeLink 标记**（如果已连接并记录中）

这样可以保持 EDF 文件精简，完整数据在日志文件中查看。

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

# Overlay 使用的眼睛（left 或 right，默认 right）
EYELINK_OVERLAY_EYE=right

# 注：文件名使用自动时间戳 (YYYYMMDD_HHMMSS)
```

## 文件保存

所有文件使用统一的时间戳命名（`YYYYMMDD_HHMMSS`）：

- **MAIC 消息**: `logdata/YYYYMMDD-HHMMSS_<request_id>.txt`
- **EDF 文件**: `logdata/eyelink_data/YYYYMMDD_HHMMSS.edf`
- **EDF 解析数据** (CSV 格式，便于查看):
  - Samples: `logdata/eyelink_data/YYYYMMDD_HHMMSS_samples.csv`
  - Events: `logdata/eyelink_data/YYYYMMDD_HHMMSS_events.csv`
  - Messages: `logdata/eyelink_data/YYYYMMDD_HHMMSS_messages.csv`
- **录屏文件**:
  - 原始: `logdata/recordings/YYYYMMDD_HHMMSS.mp4`
  - Overlay: `logdata/recordings/YYYYMMDD_HHMMSS_gaze.mp4` (带眼动轨迹)

时间戳在开始记录时自动生成，确保同一会话的所有文件使用相同的时间戳。

**CSV 文件说明**：
- `_samples.csv`: 眼动采样数据（注视点坐标、瞳孔大小等，约1000Hz）
- `_events.csv`: 眼动事件（注视、眨眼、扫视等）
- `_messages.csv`: 实验标记消息（trial_start、trial_end 等）

使用 `end` 命令自动传输、保存和处理所有文件。

## 注意事项

- 校准/验证需要 pygame 和显示器
- 文件名自动使用时间戳，无需手动配置
- dummy 模式用于无硬件测试
- 文件传输可能需要手动操作（取决于网络配置）
- 录屏功能需要安装: `pip install opencv-python mss pyedfread numpy pillow pandas`
- Overlay 处理可能需要较长时间（取决于视频长度）
- `pyedfread` 需要 SR Research EyeLink 开发工具包（Windows 平台）
- **Overlay 默认使用右眼数据**，可通过 `EYELINK_OVERLAY_EYE` 配置为 `left` 或 `right`

## API 文档

启动后访问 http://localhost:8123/docs 查看完整 API 文档。
