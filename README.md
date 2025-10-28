# MAIC JSON Service

集成 EyeLink 1000 Plus 眼动仪的数据收集服务。服务启动时自动连接 EyeLink，接收 MAIC 服务器通过 `/ingest` 端点发送的消息并实时打标记。

## 快速开始

```bash
# 使用 conda
./install.sh

# 或手动安装
conda create -n maic-service python=3.10 -y
conda activate maic-service
pip install -r requirements.txt

# 启动服务
python main.py
```

服务将在 http://localhost:8123 启动，访问 http://localhost:8123/docs 查看 API 文档。

## 项目结构

```
├── main.py              # 主服务入口
├── config.py            # 配置管理
├── models.py            # 数据模型
├── utils.py             # 工具函数
├── eyelink_manager.py   # 眼动仪管理
├── custom_control.py    # 🔧 自定义控制逻辑（用户编辑）
├── debug_eyelink.py     # EyeLink 调试工具
├── check_network.sh     # 网络检查脚本
├── requirements.txt     # 依赖包
└── config_example.env   # 配置示例
```

## 自定义控制

### 概述

`custom_control.py` 是专门为用户提供的自定义区域。在这个文件中，你可以编写自己的 EyeLink 控制逻辑，而不用担心影响主程序。

### 使用方法

1. **打开 `custom_control.py` 文件**
2. **找到你需要的示例代码**
3. **取消注释并根据需要修改**

### 功能示例

#### 1. 键盘控制

```python
# 在 custom_control.py 的 keyboard_control_example() 中取消注释
# 启用后可以通过命令行输入控制 EyeLink

EyeLink > start       # 开始记录
EyeLink > stop        # 停止记录
EyeLink > calibrate   # 校准
EyeLink > status      # 查看状态
```

#### 2. 响应 MAIC 消息

```python
# 在 handle_control_message() 函数中添加：
if event_name == "EYELINK_START_RECORDING":
    eyelink_manager.start_recording()
    return True
```

然后 MAIC 平台发送：
```json
{
  "event": "EYELINK_START_RECORDING",
  "data": {}
}
```

#### 3. 直接调用 PyLink API

```python
# 获取 tracker 对象
tracker = get_eyelink_tracker()
if tracker:
    # 发送自定义命令
    tracker.sendCommand("record_status_message 'My Custom Status'")
    tracker.sendMessage("CUSTOM_MARKER")
```

### 可用的工具函数

- `get_eyelink_tracker()` - 获取 PyLink tracker 对象
- `quick_marker(message)` - 快速发送标记
- `eyelink_manager.start_recording()` - 开始记录
- `eyelink_manager.stop_recording()` - 停止记录
- `eyelink_manager.get_status()` - 获取状态

## 核心功能

### 1. 数据接收

```bash
curl -X POST http://localhost:8123/ingest \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": {"key": "value"}}'
```

### 2. EyeLink 自动集成

服务启动时会自动：
1. 连接到 EyeLink 眼动仪（默认 IP: 100.1.1.1）
2. 开始记录眼动数据到 EDF 文件
3. 等待 MAIC 服务器发送消息

当 MAIC 服务器通过 `/ingest` 发送消息时，服务会自动将消息作为标记发送到 EyeLink。

### 3. 标记类型

- `message`: 普通消息
- `trial_start`: 试验开始
- `trial_end`: 试验结束
- `stimulus_on`: 刺激呈现
- `stimulus_off`: 刺激消失
- `response`: 被试反应
- `custom`: 自定义

## 配置

通过环境变量或 `.env` 文件配置：

```bash
# 服务配置
MAIC_PORT=8123
LOG_LEVEL=INFO

# EyeLink 配置
EYELINK_HOST_IP=100.1.1.1
EYELINK_DUMMY_MODE=false
EYELINK_SCREEN_WIDTH=1920
EYELINK_SCREEN_HEIGHT=1080
EYELINK_EDF_FILENAME=experiment.edf

# 自动连接配置
EYELINK_AUTO_CONNECT=true   # 启动时自动连接 EyeLink
EYELINK_AUTO_RECORD=true    # 连接后自动开始记录
```

## API 端点

- `GET /health` - 健康检查
- `GET /docs` - API 文档
- `POST /ingest` - 接收 MAIC 消息（核心端点）

## 注意事项

### EyeLink 相关

⚠️ **重要**：EyeLink 相关功能基于 PyLink API 文档实现，某些细节可能需要根据实际硬件调整。

- 需要安装 [EyeLink Developers Kit](https://www.sr-research.com/support/)
- 默认主机 IP: `100.1.1.1`
- EDF 文件名限制：最多 8 个字符
- 虚拟模式：设置 `EYELINK_DUMMY_MODE=true` 用于测试

### 数据流程

1. **MAIC 服务器** → 发送消息到 `http://SERVER_IP:8123/ingest`
2. **本服务** → 接收消息，保存到日志文件
3. **本服务** → 自动发送标记到 EyeLink 眼动仪
4. **EyeLink** → 在眼动数据中记录标记

消息频率完全由 MAIC 服务器控制，本服务只负责接收和转发。

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码检查
black *.py
flake8 *.py

# 运行测试
python test.py
```

## 调试工具

### 网络检查
```bash
# Unix/Linux/Mac
./check_network.sh 100.1.1.1

# 跨平台 Python 版本
python check_network.py 100.1.1.1
```

### EyeLink 测试
```bash
# 虚拟模式测试
python debug_eyelink.py --dummy

# 真实设备测试
python debug_eyelink.py --host 100.1.1.1
```

## 故障排除

### PyLink 不可用
```bash
# 安装 EyeLink Developers Kit
# 或使用虚拟模式测试
export EYELINK_DUMMY_MODE=true
python main.py
```

### 连接失败
1. 检查网络: `python check_network.py 100.1.1.1`
2. 测试连接: `python debug_eyelink.py --host 100.1.1.1`
3. 确认 EyeLink 主机开机和网络连接

## 技术栈

- **FastAPI**: Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证
- **PyLink**: EyeLink SDK (需单独安装)

## 许可证

本项目为私有项目。使用 EyeLink 功能需遵循 SR Research 许可协议。

## 版本

v1.0.0 - 2025-10-27
