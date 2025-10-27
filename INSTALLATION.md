# 安装指南

本文档介绍如何安装和配置 MAIC JSON Service with EyeLink Integration。

## 系统要求

- Python 3.8 或更高版本
- pip (Python 包管理器)
- EyeLink Developers Kit (用于眼动仪功能)

## 安装步骤

### 1. 克隆或下载项目

```bash
cd /Users/liujiany/work/test
```

### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. 安装基础依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 EyeLink Developers Kit

EyeLink 的 PyLink 库需要单独安装：

1. 访问 SR Research 支持论坛: https://www.sr-research.com/support/
2. 下载并安装 EyeLink Developers Kit
3. 安装后，PyLink 将自动可用

**注意**: 如果不使用眼动仪功能，可以跳过此步骤。服务会自动检测 PyLink 是否可用，并在不可用时禁用相关功能。

### 5. 配置环境变量（可选）

复制配置示例文件：

```bash
cp config_example.env .env
```

编辑 `.env` 文件，根据需要修改配置：

```bash
# 基础服务配置
MAIC_PORT=8123

# EyeLink 眼动仪配置
EYELINK_HOST_IP=100.1.1.1
EYELINK_DUMMY_MODE=false
EYELINK_SCREEN_WIDTH=1920
EYELINK_SCREEN_HEIGHT=1080
EYELINK_EDF_FILENAME=experiment.edf

# 轮询配置
POLLING_ENABLED=true
POLLING_INTERVAL=0.1
```

如果使用 `.env` 文件，需要安装 python-dotenv：

```bash
pip install python-dotenv
```

并在 `main.py` 开头添加：

```python
from dotenv import load_dotenv
load_dotenv()
```

### 6. 验证安装

运行测试脚本验证安装：

```bash
python test_core_modules.py
```

如果看到以下输出，说明安装成功：

```
🎉 所有核心模块测试通过！重构成功！
```

## 开发环境安装

如果您需要开发或贡献代码，请安装开发依赖：

```bash
pip install -r requirements-dev.txt
```

## 启动服务

### 基本启动

```bash
python main.py
```

### 使用 uvicorn 启动（推荐用于生产环境）

```bash
uvicorn main:app --host 0.0.0.0 --port 8123
```

### 带热重载的开发模式

```bash
uvicorn main:app --host 0.0.0.0 --port 8123 --reload
```

## 验证服务

服务启动后，访问以下 URL 验证：

```bash
# 健康检查
curl http://localhost:8123/health

# 查看 API 文档
# 在浏览器中打开: http://localhost:8123/docs
```

## 故障排除

### 问题 1: 找不到 fastapi 模块

**解决方案**:
```bash
pip install fastapi uvicorn
```

### 问题 2: 找不到 pylink 模块

**解决方案**:
- 确保已安装 EyeLink Developers Kit
- 检查 Python 路径设置
- 或者设置 `EYELINK_DUMMY_MODE=true` 使用虚拟模式

### 问题 3: 端口已被占用

**解决方案**:
```bash
# 修改端口
export MAIC_PORT=8124
python main.py
```

### 问题 4: 权限错误

**解决方案**:
```bash
# 确保 logdata 目录有写权限
chmod 755 logdata
```

## 运行示例

安装完成后，可以运行示例程序：

```bash
# 运行 EyeLink 集成示例
python eyelink_example.py
```

## 卸载

如果需要卸载：

```bash
# 停用虚拟环境
deactivate

# 删除虚拟环境
rm -rf venv

# 删除 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## 更新

更新到最新版本：

```bash
# 更新依赖
pip install -r requirements.txt --upgrade

# 运行测试
python test_core_modules.py
```

## 技术支持

如果遇到问题：

1. 查看日志文件: `log/service.out`
2. 检查 README 文档
3. 运行测试脚本诊断问题
4. 查看 SR Research 支持论坛（PyLink 相关问题）

## 生产环境部署建议

1. **使用 systemd 服务**（Linux）
2. **使用进程管理器**（如 supervisor, pm2）
3. **配置反向代理**（如 nginx）
4. **启用日志轮转**
5. **配置防火墙规则**
6. **设置自动重启机制**

详细的生产环境部署指南，请参考项目文档。
