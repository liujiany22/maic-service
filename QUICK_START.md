# 快速开始指南

5 分钟快速上手 MAIC JSON Service with EyeLink Integration。

## 📦 安装（1 分钟）

```bash
# 方式 1: 使用安装脚本（推荐）
./install.sh

# 方式 2: 手动安装
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## 🚀 启动服务（30 秒）

```bash
python main.py
```

服务将在 http://localhost:8123 启动。

## ✅ 验证安装（30 秒）

```bash
# 测试 1: 健康检查
curl http://localhost:8123/health

# 测试 2: 查看 API 文档
open http://localhost:8123/docs

# 测试 3: 运行测试
python test_core_modules.py
```

## 🎯 基本使用（3 分钟）

### 1. 连接眼动仪

```bash
curl -X POST http://localhost:8123/eyelink/connect
```

### 2. 开始记录

```bash
curl -X POST http://localhost:8123/eyelink/start_recording
```

### 3. 发送标记

```bash
curl -X POST http://localhost:8123/eyelink/marker \
  -H "Content-Type: application/json" \
  -d '{
    "marker_type": "trial_start",
    "message": "Trial 1",
    "trial_id": "001"
  }'
```

### 4. 停止记录

```bash
curl -X POST http://localhost:8123/eyelink/stop_recording
```

### 5. 断开连接

```bash
curl -X POST http://localhost:8123/eyelink/disconnect
```

## 🐍 Python 示例

```python
import requests

BASE_URL = "http://localhost:8123"

# 连接
requests.post(f"{BASE_URL}/eyelink/connect")

# 开始记录
requests.post(f"{BASE_URL}/eyelink/start_recording")

# 发送标记
requests.post(f"{BASE_URL}/eyelink/marker", json={
    "marker_type": "trial_start",
    "message": "Trial 1",
    "trial_id": "001"
})

# 发送外部数据（自动标记）
requests.post(f"{BASE_URL}/ingest", json={
    "event": "stimulus_presented",
    "data": {"stimulus_id": "img_001"}
})

# 停止记录
requests.post(f"{BASE_URL}/eyelink/stop_recording")
```

## 📝 标记类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `message` | 普通消息 | 一般性标记 |
| `trial_start` | 试验开始 | 标记试验开始 |
| `trial_end` | 试验结束 | 标记试验结束 |
| `stimulus_on` | 刺激呈现 | 图片/声音呈现 |
| `stimulus_off` | 刺激消失 | 刺激移除 |
| `response` | 被试反应 | 按键/眼动反应 |
| `custom` | 自定义 | 任意自定义标记 |

## ⚙️ 配置（可选）

创建 `.env` 文件：

```bash
MAIC_PORT=8123
EYELINK_HOST_IP=100.1.1.1
EYELINK_DUMMY_MODE=false
POLLING_ENABLED=true
```

## 🔍 常用命令

```bash
# 查看眼动仪状态
curl http://localhost:8123/eyelink/status

# 查看轮询状态
curl http://localhost:8123/polling/status

# 查看所有路由
curl http://localhost:8123/openapi.json
```

## 📱 API 文档

访问 http://localhost:8123/docs 查看交互式 API 文档。

## 🆘 遇到问题？

```bash
# 1. 运行测试诊断
python test_core_modules.py

# 2. 查看日志
tail -f log/service.out

# 3. 查看详细文档
cat INSTALLATION.md
```

## 📚 下一步

- 查看完整文档: `README.md`
- 运行完整示例: `python eyelink_example.py`
- 自定义轮询逻辑: 编辑 `data_poller.py`
- 添加新的 API: 编辑 `api_routes.py`

## 💡 小贴士

1. **虚拟模式**: 如果没有眼动仪，设置 `EYELINK_DUMMY_MODE=true`
2. **自动重启**: 使用 `uvicorn main:app --reload` 开发时自动重载
3. **后台运行**: 使用 `nohup python main.py &` 后台运行
4. **查看进程**: 使用 `ps aux | grep main.py` 查看运行状态

---

🎉 恭喜！您已经掌握了基本用法。

需要更多帮助？查看 [README.md](README.md) 或 [INSTALLATION.md](INSTALLATION.md)。
