# Conda 环境安装指南

本文档专门介绍如何使用 conda 安装和配置 MAIC JSON Service。

## 前提条件

- 已安装 Anaconda 或 Miniconda
- Python 3.8 或更高版本

## 快速安装

### 方式 1: 使用安装脚本（推荐）

```bash
./install.sh
```

脚本会自动检测 conda，并询问是否使用 conda 创建环境。

### 方式 2: 手动创建 conda 环境

```bash
# 1. 创建 conda 环境
conda create -n maic-service python=3.10 -y

# 2. 激活环境
conda activate maic-service

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建必要的目录
mkdir -p logdata log

# 5. 运行测试
python test_core_modules.py
```

## 详细步骤

### 1. 创建 Conda 环境

```bash
# 创建名为 maic-service 的环境，指定 Python 版本
conda create -n maic-service python=3.10 -y
```

**选择 Python 版本的建议：**
- Python 3.10（推荐）：稳定且兼容性好
- Python 3.11：最新特性
- Python 3.8/3.9：兼容旧系统

### 2. 激活环境

```bash
conda activate maic-service
```

**验证激活：**
```bash
# 检查 Python 版本
python --version

# 检查环境名称
conda env list
```

### 3. 安装依赖包

```bash
# 使用 pip 安装（推荐）
pip install -r requirements.txt

# 或者分步安装
pip install fastapi uvicorn pydantic requests
```

**为什么使用 pip 而不是 conda install？**
- FastAPI 生态系统在 PyPI 上更新更快
- 某些包在 conda 仓库中可能版本较旧
- pip 和 conda 可以很好地配合使用

### 4. 验证安装

```bash
# 运行测试脚本
python test_core_modules.py

# 检查已安装的包
conda list
# 或
pip list
```

### 5. 启动服务

```bash
python main.py
```

## Conda 环境管理

### 查看所有环境

```bash
conda env list
# 或
conda info --envs
```

### 激活/退出环境

```bash
# 激活环境
conda activate maic-service

# 退出环境
conda deactivate
```

### 导出环境配置

```bash
# 导出为 YAML 文件（conda 特有格式）
conda env export > environment.yml

# 导出 pip 依赖
pip freeze > requirements.txt
```

### 从配置文件创建环境

```bash
# 从 environment.yml 创建
conda env create -f environment.yml

# 从 requirements.txt 创建
conda create -n maic-service python=3.10 -y
conda activate maic-service
pip install -r requirements.txt
```

### 更新环境

```bash
# 更新所有包
conda activate maic-service
pip install -r requirements.txt --upgrade

# 更新特定包
pip install fastapi --upgrade
```

### 删除环境

```bash
# 退出环境（如果已激活）
conda deactivate

# 删除环境
conda env remove -n maic-service
```

### 清理 Conda 缓存

```bash
# 清理未使用的包和缓存
conda clean --all -y
```

## 开发环境设置

### 安装开发工具

```bash
conda activate maic-service
pip install -r requirements-dev.txt
```

### IDE 配置

#### VS Code

1. 安装 Python 扩展
2. 选择解释器：
   - 按 `Cmd+Shift+P` (Mac) 或 `Ctrl+Shift+P` (Windows/Linux)
   - 输入 "Python: Select Interpreter"
   - 选择 `maic-service` 环境

#### PyCharm

1. 打开 `Settings/Preferences` → `Project` → `Python Interpreter`
2. 点击齿轮图标 → `Add`
3. 选择 `Conda Environment` → `Existing environment`
4. 选择 `maic-service` 环境

## 常见问题

### Q1: conda 命令未找到

**解决方案：**
```bash
# 初始化 conda（仅需一次）
conda init bash
# 或
conda init zsh

# 重启终端或重新加载配置
source ~/.bashrc  # 或 ~/.zshrc
```

### Q2: 激活环境后仍使用系统 Python

**解决方案：**
```bash
# 检查 conda 初始化
conda init

# 重启终端
# 确认环境已激活
which python
```

### Q3: pip 安装包到系统而不是 conda 环境

**解决方案：**
```bash
# 确保环境已激活
conda activate maic-service

# 验证 pip 位置
which pip  # 应该指向 conda 环境

# 使用 python -m pip 明确指定
python -m pip install -r requirements.txt
```

### Q4: conda 环境和 pip 包冲突

**解决方案：**
```bash
# 优先使用 pip 安装 Python 包
pip install <package>

# 只有在必要时才使用 conda install
# 例如：系统级依赖或 C 扩展
conda install -c conda-forge <package>
```

### Q5: PyLink 在 conda 环境中无法导入

**解决方案：**
1. 确保已安装 EyeLink Developers Kit
2. 检查 Python 路径：
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```
3. 如果需要，设置虚拟模式：
   ```bash
   export EYELINK_DUMMY_MODE=true
   python main.py
   ```

## 性能优化

### 使用 Conda Pack 打包环境

```bash
# 安装 conda-pack
conda install -c conda-forge conda-pack

# 打包环境
conda activate maic-service
conda pack -n maic-service -o maic-service.tar.gz

# 在另一台机器上解包
mkdir -p maic-service
tar -xzf maic-service.tar.gz -C maic-service
source maic-service/bin/activate
```

### 使用 Mamba 加速（可选）

```bash
# 安装 mamba
conda install mamba -c conda-forge

# 使用 mamba 代替 conda（更快）
mamba create -n maic-service python=3.10 -y
mamba activate maic-service
```

## 生产环境部署

### 创建精简环境

```bash
# 只安装必需的包
conda create -n maic-service-prod python=3.10 -y
conda activate maic-service-prod
pip install --no-cache-dir -r requirements.txt
```

### 使用 conda 启动服务

```bash
# 创建启动脚本
cat > start_service.sh << 'EOF'
#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate maic-service
python main.py
EOF

chmod +x start_service.sh
./start_service.sh
```

## Conda vs venv 对比

| 特性 | Conda | venv |
|------|-------|------|
| 跨平台 | ✅ 优秀 | ✅ 良好 |
| 包管理 | ✅ Python + 系统包 | ⚠️ 仅 Python |
| 安装速度 | ⚠️ 较慢 | ✅ 快速 |
| 依赖解决 | ✅ 强大 | ⚠️ 基础 |
| 磁盘占用 | ⚠️ 较大 | ✅ 较小 |
| 适用场景 | 科学计算/ML | 轻量级项目 |

## 推荐配置

### 最小配置（仅运行服务）

```bash
conda create -n maic-service python=3.10 -y
conda activate maic-service
pip install fastapi uvicorn pydantic requests
```

### 标准配置（包含开发工具）

```bash
conda create -n maic-service python=3.10 -y
conda activate maic-service
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 完整配置（包含 Jupyter）

```bash
conda create -n maic-service python=3.10 jupyter -y
conda activate maic-service
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 总结

使用 conda 的优势：
- ✅ 更好的依赖管理
- ✅ 方便的环境切换
- ✅ 跨平台一致性
- ✅ 易于分享和重现

使用 `install.sh` 脚本可以自动处理大部分配置，推荐使用！

如有问题，请参考 [INSTALLATION.md](INSTALLATION.md) 或 [README.md](README.md)。
