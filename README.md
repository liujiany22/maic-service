# MAIC JSON Service

集成 EyeLink 1000 Plus 眼动仪的数据收集服务，支持实时标记和轮询机制。

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
├── data_poller.py       # 数据轮询器
├── api_routes.py        # API 路由
├── requirements.txt     # 依赖包
└── config_example.env   # 配置示例
```

## 核心功能

### 1. 数据接收

```bash
curl -X POST http://localhost:8123/ingest \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": {"key": "value"}}'
```

### 2. EyeLink 集成

```python
import requests

# 连接眼动仪
requests.post("http://localhost:8123/eyelink/connect")

# 开始记录
requests.post("http://localhost:8123/eyelink/start_recording")

# 发送标记
requests.post("http://localhost:8123/eyelink/marker", json={
    "marker_type": "trial_start",
    "message": "Trial 1",
    "trial_id": "001"
})

# 停止记录
requests.post("http://localhost:8123/eyelink/stop_recording")
```

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

# 轮询配置
POLLING_ENABLED=true
POLLING_INTERVAL=0.1
```

## API 端点

### 基础

- `GET /health` - 健康检查
- `GET /docs` - API 文档
- `POST /ingest` - 接收数据

### EyeLink

- `GET /eyelink/status` - 查看状态
- `POST /eyelink/connect` - 连接
- `POST /eyelink/start_recording` - 开始记录
- `POST /eyelink/stop_recording` - 停止记录
- `POST /eyelink/marker` - 发送标记

### 轮询

- `GET /polling/status` - 查看状态
- `POST /polling/start` - 启动轮询
- `POST /polling/stop` - 停止轮询

## 注意事项

### EyeLink 相关

⚠️ **重要**：EyeLink 相关功能基于 PyLink API 文档实现，某些细节可能需要根据实际硬件调整。

- 需要安装 [EyeLink Developers Kit](https://www.sr-research.com/support/)
- 默认主机 IP: `100.1.1.1`
- EDF 文件名限制：最多 8 个字符
- 虚拟模式：设置 `EYELINK_DUMMY_MODE=true` 用于测试

### 数据轮询

要自定义轮询逻辑，编辑 `data_poller.py` 中的 `_fetch_external_data` 方法：

```python
def _fetch_external_data(self):
    # 实现你的数据获取逻辑
    # 例如：从数据库查询、调用 API 等
    pass
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码检查
black *.py
flake8 *.py

# 运行测试
python test_core_modules.py
```

## 故障排除

### PyLink 导入失败

```bash
# 安装 EyeLink Developers Kit 或使用虚拟模式
export EYELINK_DUMMY_MODE=true
python main.py
```

### 端口被占用

```bash
export MAIC_PORT=8124
python main.py
```

### 连接失败

检查：
1. EyeLink 主机是否开启
2. 网络连接是否正常
3. IP 地址是否正确

## 技术栈

- **FastAPI**: Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证
- **PyLink**: EyeLink SDK (需单独安装)

## 许可证

本项目为私有项目。使用 EyeLink 功能需遵循 SR Research 许可协议。

## 版本

v1.0.0 - 2025-10-27
