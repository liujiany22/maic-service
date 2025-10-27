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
├── api_routes.py        # API 路由
├── debug_eyelink.py     # EyeLink 调试工具
├── check_network.sh     # 网络检查脚本
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

### 2. EyeLink 自动集成

服务启动时会自动：
1. 连接到 EyeLink 眼动仪（默认 IP: 100.1.1.1）
2. 开始记录眼动数据到 EDF 文件
3. 等待 MAIC 服务器发送消息

当 MAIC 服务器通过 `/ingest` 发送消息时，服务会自动将消息作为标记发送到 EyeLink。

也可以手动控制：

```python
import requests

# 手动连接眼动仪（如果自动连接失败）
requests.post("http://localhost:8123/eyelink/connect")

# 手动开始记录
requests.post("http://localhost:8123/eyelink/start_recording")

# 手动发送标记
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
EYELINK_EDF_FILENAME=experiment.edf

# 自动连接配置
EYELINK_AUTO_CONNECT=true   # 启动时自动连接 EyeLink
EYELINK_AUTO_RECORD=true    # 连接后自动开始记录
```

## API 端点

### 基础

- `GET /health` - 健康检查
- `GET /docs` - API 文档
- `POST /ingest` - 接收数据

### EyeLink

- `GET /eyelink/status` - 查看状态
- `POST /eyelink/connect` - 手动连接（通常不需要，启动时自动连接）
- `POST /eyelink/disconnect` - 断开连接
- `POST /eyelink/start_recording` - 手动开始记录（通常不需要，自动开始）
- `POST /eyelink/stop_recording` - 停止记录
- `POST /eyelink/marker` - 手动发送标记

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

项目提供了专门的调试工具帮助排查 EyeLink 连接问题：

### 1. 网络连接检查

```bash
./check_network.sh [IP地址]

# 示例
./check_network.sh 100.1.1.1
```

此脚本会自动检查：
- Ping 连通性
- 本地网络接口
- 路由配置
- ARP 缓存

### 2. EyeLink 连接测试

```bash
# 测试真实设备
python debug_eyelink.py --host 100.1.1.1

# 测试虚拟模式
python debug_eyelink.py --dummy

# 自定义屏幕尺寸
python debug_eyelink.py --host 100.1.1.1 --width 1920 --height 1080
```

此脚本会：
1. 检查 PyLink 可用性
2. 显示连接参数
3. 尝试连接 EyeLink
4. 测试发送标记
5. 断开连接

所有步骤都有详细的调试信息输出。

### 3. 日志级别

如需更详细的调试信息：

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 故障排除

### PyLink 导入失败

**症状**: 启动时提示 "PyLink library not available"

**解决方案**:
```bash
# 1. 安装 EyeLink Developers Kit
# 从 https://www.sr-research.com/support/ 下载

# 2. 验证安装
python -c "import pylink; print(pylink)"

# 3. 或使用虚拟模式测试
export EYELINK_DUMMY_MODE=true
python main.py
```

### 端口被占用

**症状**: "Address already in use"

**解决方案**:
```bash
export MAIC_PORT=8124
python main.py
```

### EyeLink 连接失败

**症状**: 调用 `/eyelink/connect` 返回错误

**调试步骤**:

1. **检查网络连接**
   ```bash
   ./check_network.sh 100.1.1.1
   ```

2. **运行调试脚本**
   ```bash
   python debug_eyelink.py --host 100.1.1.1
   ```

3. **检查常见问题**:
   - [ ] EyeLink 主机是否开机？
   - [ ] 网络线是否连接？
   - [ ] IP 地址是否正确？（在 EyeLink 主机上确认）
   - [ ] 防火墙是否阻止连接？
   - [ ] PyLink 是否正确安装？

4. **查看详细日志**:
   ```bash
   export LOG_LEVEL=DEBUG
   python main.py
   ```
   
   然后查看 `log/service.out` 获取详细错误信息

5. **尝试虚拟模式**（验证代码逻辑）:
   ```bash
   python debug_eyelink.py --dummy
   ```

### 标记发送失败

**可能原因**:
- 未处于 RECORDING 状态
- Tracker 对象未初始化
- 消息格式不正确

**解决方案**:
1. 检查状态: `GET /eyelink/status`
2. 确保先调用 `POST /eyelink/start_recording`
3. 查看 DEBUG 日志确认消息格式

## 技术栈

- **FastAPI**: Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证
- **PyLink**: EyeLink SDK (需单独安装)

## 许可证

本项目为私有项目。使用 EyeLink 功能需遵循 SR Research 许可协议。

## 版本

v1.0.0 - 2025-10-27
