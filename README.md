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

服务启动后使用以下命令：

```
> c              # 校准
> v              # 验证  
> d              # 漂移校正
> start          # 开始记录
> marker TEST    # 发送标记
> end            # 结束并保存
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
EYELINK_EDF_FILENAME=test.edf
EYELINK_AUTO_CONNECT=true
```

## 文件保存

- 接收的消息保存在 `logdata/` 目录
- EDF 文件保存在 `logdata/eyelink_data/` 目录
- 文件名格式: `YYYYMMDD_HHMMSS_test.edf`

## 调试

### 网络检查

```bash
python check_network.py [IP地址]
```

### EyeLink 测试

```bash
python debug_eyelink.py --host 100.1.1.1
```

## 注意事项

- 校准/验证需要 pygame 和显示器
- EDF 文件名默认为 `test.edf`（可在 `.env` 修改）
- dummy 模式用于无硬件测试
- 文件传输可能需要手动操作（取决于网络配置）

## API 文档

启动后访问 http://localhost:8123/docs 查看完整 API 文档。
